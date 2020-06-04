import os
import time
import unittest
import uuid
from importlib.machinery import SourceFileLoader
from importlib.util import spec_from_loader, module_from_spec

import dxpy
import dxpy.api
import dxpy.app_builder
from dxpy.exceptions import DXAPIError, DXJobFailureError


#  https://stackoverflow.com/questions/2601047/import-a-python-module-without-the-py-extension
def import_module(module_name: str, module_path: str):
    spec = spec_from_loader(module_name, SourceFileLoader(module_name, module_path))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


src_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
find_cwic_jobs = import_module("dx-find-cwic-jobs", f"{src_dir}/resources/usr/local/bin/dx-find-cwic-jobs")
DX_PROJECT_ID = 'project-BzQf6k80V3bJk7x0yv6z82j7'
TEST_TIMESTAMP = str(int(time.time()))
PROJECT_DX = dxpy.DXProject(DX_PROJECT_ID)
TEST_FOLDER = '/cwic/test'


class TestCwic(unittest.TestCase):
    applet_id = None

    @classmethod
    def setUpClass(cls):

        print("Runing make to create a resource dir")
        dxpy.app_builder.build(src_dir)

        print("Uploading the app resources to the platform")
        bundled_resources = dxpy.app_builder.upload_resources(
            src_dir, project=DX_PROJECT_ID, folder=TEST_FOLDER,
        )

        try:
            app_name = os.path.basename(os.path.abspath(src_dir)) + "_test"
        except OSError:
            app_name = "test_app"

        print("Uploading the applet to the platform")
        cls.applet_basename = app_name + "_" + str(uuid.uuid4())
        cls.applet_id, _ignored_applet_spec = dxpy.app_builder.upload_applet(
            src_dir, bundled_resources, override_name=cls.applet_basename,
            overwrite=True, project=DX_PROJECT_ID, override_folder=TEST_FOLDER
        )
        cls.applet_dx = dxpy.DXApplet(cls.applet_id)

    @classmethod
    def tearDownClass(cls):
        print("Clean up by removing the app we created.")
        try:
            dxpy.api.container_remove_objects(
                DX_PROJECT_ID, {"objects": [cls.applet_id]}
            )
        except (DXAPIError, DXJobFailureError) as e:
            print("Error removing {} during cleanup; ignoring.".format(cls.applet_id))
            print(e)

    def test_run_no_input_params(self):
        input_args = {}
        job = self.applet_dx.run(
            input_args,
            folder=TEST_FOLDER,
            project=DX_PROJECT_ID,
            name=self.applet_basename
        )
        try:
            job.wait_on_done()
            # if job continued, fail this test
            raise Exception("Job should have failed with DXJobFailureError")
        except dxpy.exceptions.DXJobFailureError:
            failure_mesg = job.describe()["failureMessage"]
            self.assertIn("Error while checking if cwic will be run interactively", failure_mesg)

    def test_get_column_widths(self):
        example_table = [["max-length-13", "short", "short", "same-length-longest"],
                         ["shorter", "longer-string-another-characters---", "", "same-length-longest"],
                         ["string", "example", "very-long-string-this-is-longest", "c"],
                         ["...", "....", ".....", "CAPITAL_CHARS"]]
        expected_result = [13, 35, 32, 19]
        expected_result_max_width_20 = [13, 20, 20, 19]
        assert find_cwic_jobs.get_column_widths(example_table) == expected_result, "max columns widths are different than expected"
        assert find_cwic_jobs.get_column_widths(example_table, max_width=20) == expected_result_max_width_20, "max columns widths are different than expected"

    def test_create_file_in_mounted_project(self):
        """ Test that a file created in a mounted project in cwic is
        accessible from the platform"""
        DX_PROJECT_NAME = PROJECT_DX.describe()["name"]

        file_name = "test_foo_{}.txt".format(TEST_TIMESTAMP)
        input_args = {
            "cmd": "touch \"/project/{}{}/{}\"".format(DX_PROJECT_NAME, TEST_FOLDER, file_name)
        }
        job = self.applet_dx.run(
            input_args,
            folder=TEST_FOLDER,
            project=DX_PROJECT_ID,
            name=self.applet_basename
        )
        print("Waiting for the job {j_id} to complete".format(j_id=job.get_id()))
        job.wait_on_done()
        list_folder = dxpy.DXProject(DX_PROJECT_ID).list_folder(TEST_FOLDER, describe={"fields": {"id": True, "name": True}})
        file_names = [i["describe"]["name"] for i in list_folder["objects"]]
        self.assertIn(file_name, file_names)

        # Clean up: get the ID of the created file and remove it
        f_ids = [f["describe"]["id"] for f in list_folder["objects"] if f["describe"]["name"] == file_name and f["describe"]["id"].startswith("file")]
        if f_ids:
            dxpy.api.container_remove_objects(
                DX_PROJECT_ID, {"objects": f_ids}
            )

    def test_check_home_directory(self):
        """ Test that the home directory inside Docker is /home/cwic """

        input_args = {
            "cmd": 'env; if [ "$HOME" != "/home/cwic" ]; then exit 1; fi'
        }
        job = self.applet_dx.run(
            input_args,
            folder=TEST_FOLDER,
            project=DX_PROJECT_ID,
            name=self.applet_basename
        )
        print("Waiting for the job {j_id} to complete".format(j_id=job.get_id()))
        job.wait_on_done()

if __name__ == '__main__':
    unittest.main()
