import os
import time
import unittest
import dxpy
import dxpy.api
import dxpy.app_builder
from contextlib import contextmanager
from dxpy.exceptions import DXAPIError


src_dir = os.path.join(os.path.dirname(__file__), "..")
DX_PROJECT_ID = 'project-BzQf6k80V3bJk7x0yv6z82j7'
TEST_TIMESTAMP = str(int(time.time()))
PROJECT_DX = dxpy.DXProject(DX_PROJECT_ID)
TEST_FOLDER = '/cwic' + TEST_TIMESTAMP

class TestCwic(unittest.TestCase):
    applet_id = None

    @classmethod
    def setUpClass(cls):
        print("Creating the folder {}".format(TEST_FOLDER))
        PROJECT_DX.new_folder(folder=TEST_FOLDER, parents=True)

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
        cls.applet_basename = app_name + "_" + TEST_TIMESTAMP
        cls.applet_id, _ignored_applet_spec = dxpy.app_builder.upload_applet(
            src_dir, bundled_resources, override_name=cls.applet_basename,
            overwrite=True, project=DX_PROJECT_ID, override_folder=TEST_FOLDER
        )
        cls.applet_dx = dxpy.DXApplet(cls.applet_id)
 
    @classmethod
    def tearDownClass(cls):
        print("Clean up by removing the test folder we created")
        try:
            PROJECT_DX.remove_folder(folder=TEST_FOLDER, recurse=True)
        except DXAPIError as e:
            print("Error during cleanup; ignoring.")
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

    # @unittest.skip(reason="unskip once https://jira.internal.dnanexus.com/browse/DEVEX-1584 is fixed.")
    # def test_create_file_in_mounted_project(self):
    #     DX_PROJECT_NAME = PROJECT_DX.describe()["name"]

    #     file_name = "test_foo_{}.txt".format(TEST_TIMESTAMP)
    #     input_args = {
    #         "cmd": "touch \"/project/{}{}/{}\"".format(DX_PROJECT_NAME, TEST_FOLDER, file_name)
    #     }
    #     job = self.applet_dx.run(
    #         input_args,
    #         folder=TEST_FOLDER,
    #         project=DX_PROJECT_ID,
    #         name=self.applet_basename
    #     )
    #     print("Waiting for the job {j_id} to complete".format(j_id=job.get_id()))
    #     job.wait_on_done()
    #     list_folder = dxpy.DXProject(DX_PROJECT_ID).list_folder(TEST_FOLDER, describe={"fields": {"name": True}})
    #     folder_names = [i["describe"]["name"] for i in list_folder["objects"]]
    #     self.assertIn(file_name, folder_names)


if __name__ == '__main__':
    unittest.main()
