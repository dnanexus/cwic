#!/usr/bin/env python3

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

from test_utils import test_utils as TU


#  https://stackoverflow.com/questions/2601047/import-a-python-module-without-the-py-extension
def import_module(module_name: str, module_path: str):
    spec = spec_from_loader(module_name, SourceFileLoader(module_name, module_path))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

DX_CWIC_PROJECT_ID = os.environ.get('DX_CWIC_PROJECT_ID', 'project-BzQf6k80V3bJk7x0yv6z82j7')
src_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
find_cwic_jobs = import_module("dx-find-cwic-jobs", f"{src_dir}/resources/usr/local/bin/dx-find-cwic-jobs")
TEST_TIMESTAMP = str(int(time.time()))
PROJECT_DX = dxpy.DXProject(DX_CWIC_PROJECT_ID)
PROJECT_NAME = PROJECT_DX.name
TEST_FOLDER = '/cwic/'

print(f"Running tests in {PROJECT_NAME}")

class TestCwic(unittest.TestCase):
    applet_id = None

    @classmethod
    def setUpClass(cls):

        print("Creating test folder")
        try:
            PROJECT_DX.new_folder(TEST_FOLDER)
        except dxpy.DXAPIError:
            print(f"Folder {TEST_FOLDER} already exists")
        print(f"Created: {TEST_FOLDER}")

        print("Runing make to create a resource dir")
        dxpy.app_builder.build(src_dir)

        print("Uploading the app resources to the platform")
        bundled_resources = dxpy.app_builder.upload_resources(
            src_dir, project=DX_CWIC_PROJECT_ID, folder=TEST_FOLDER,
        )

        try:
            app_name = os.path.basename(os.path.abspath(src_dir)) + "_test"
        except OSError:
            app_name = "test_app"

        print("Uploading the applet to the platform")
        cls.applet_basename = app_name + "_" + str(uuid.uuid4())
        cls.applet_id, _ignored_applet_spec = dxpy.app_builder.upload_applet(
            src_dir, bundled_resources, override_name=cls.applet_basename,
            overwrite=True, project=DX_CWIC_PROJECT_ID, override_folder=TEST_FOLDER
        )
        cls.applet_dx = dxpy.DXApplet(cls.applet_id)

    @classmethod
    def tearDownClass(cls):
        print("Clean up by removing the app we created.")
        try:
            dxpy.api.container_remove_objects(
                DX_CWIC_PROJECT_ID, {"objects": [cls.applet_id]}
            )
        except (DXAPIError, DXJobFailureError) as e:
            print("Error removing {} during cleanup; ignoring.".format(cls.applet_id))
            print(e)

    def test_get_column_widths(self):
        example_table = [["max-length-13", "short", "short", "same-length-longest"],
                         ["shorter", "longer-string-another-characters---", "", "same-length-longest"],
                         ["string", "example", "very-long-string-this-is-longest", "c"],
                         ["...", "....", ".....", "CAPITAL_CHARS"]]
        expected_result = [13, 35, 32, 19]
        expected_result_max_width_20 = [13, 20, 20, 19]
        assert find_cwic_jobs.get_column_widths(example_table) == expected_result, "max columns widths are different than expected"
        assert find_cwic_jobs.get_column_widths(example_table, max_width=20) == expected_result_max_width_20, "max columns widths are different than expected"

    def test_run_interactive_mode_without_allowssh(self):
        """Test that options --ssh or --allow-ssh are used when CWIC
        is run in an interactive mode"""
        input_args = {}
        job = self.applet_dx.run(
            input_args,
            folder=TEST_FOLDER,
            project=DX_CWIC_PROJECT_ID,
            name=self.applet_basename
        )
        try:
            job.wait_on_done()
            # if job continued, fail this test
            raise Exception("Job should have failed with DXJobFailureError")
        except dxpy.exceptions.DXJobFailureError:
            failure_mesg = job.describe()["failureMessage"]
            self.assertIn("Error while checking if cwic will be run interactively", failure_mesg)

    def test_upload_without_credentials(self):
        file_name = f"test_no_credentials_{TEST_TIMESTAMP}.txt"
        input_args = {
            "cmd": f"dx cd {TEST_FOLDER}; touch {file_name}; dx upload {file_name};"
        }
        job = self.applet_dx.run(
            input_args,
            folder=TEST_FOLDER,
            project=DX_CWIC_PROJECT_ID,
            name=self.applet_basename
        )
        job.wait_on_done()
        TU.check_if_exists_and_delete(file_name, DX_CWIC_PROJECT_ID, TEST_FOLDER)

    def test_project_is_not_mounted(self):
        file_name = f"test_no_credentials_{TEST_TIMESTAMP}.txt"
        input_args = {
            "cmd": f"touch \"/project/{PROJECT_NAME}{TEST_FOLDER}/{file_name}\""
        }
        job = self.applet_dx.run(
            input_args,
            folder=TEST_FOLDER,
            project=DX_CWIC_PROJECT_ID,
            name=self.applet_basename
        )
        TU.check_job_is_unsuccessful(job)

    def test_create_file_in_mounted_project_with_write_access(self):
        """ Test that a file created in a mounted project in cwic is
        accessible from the platform"""

        file_name = "test_foo_{}.txt".format(TEST_TIMESTAMP)
        input_args = {
            "cmd": f"touch \"/project/{PROJECT_NAME}{TEST_FOLDER}/{file_name}\"",
            "project_mount_options": "-w"
        }
        job = self.applet_dx.run(
            input_args,
            folder=TEST_FOLDER,
            project=DX_CWIC_PROJECT_ID,
            name=self.applet_basename
        )
        print("Waiting for the job {j_id} to complete".format(j_id=job.get_id()))
        job.wait_on_done()
        TU.check_if_exists_and_delete(file_name, DX_CWIC_PROJECT_ID, TEST_FOLDER)

    def test_check_home_directory(self):
        """ Test that the home directory inside Docker is /home/cwic """

        input_args = {
            "cmd": 'env; if [ "$HOME" != "/home/cwic" ]; then exit 1; fi'
        }
        job = self.applet_dx.run(
            input_args,
            folder=TEST_FOLDER,
            project=DX_CWIC_PROJECT_ID,
            name=self.applet_basename
        )
        print("Waiting for the job {j_id} to complete".format(j_id=job.get_id()))
        job.wait_on_done()

    @unittest.skip("Skip due to missing files: samtools & bam")
    def test_read_file_in_mounted_project(self):
        """ Test that files can be read (with samtools) from a mounted project,
        dx uploaded, and then read again"""

        bash_script="""
#!/bin/bash

set -xe
proj="PROJECT_PLACEHOLDER"
samtools_path="/project/$proj/samtools"
bam_path="/project/$proj/data_files/Small BAM/SRR504516_small.bam"
uuid=$(python3 -c 'import uuid; print(uuid.uuid4())')

cp "$samtools_path" /usr/bin/
chmod +x /usr/bin/samtools

# Removing 20 21 22 since they result in files 100-200M
chromosomes="1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 X Y MT"

# Take md5 sum of each sorted bam and compare to the md5sum
# when they are read in the dxfuse-mounted project
for chr in $chromosomes; do
  bam_name="${uuid}_bam_${chr}.bam"
  samtools view -b "${bam_path}" "${chr}" -o /scratch/"$bam_name"
  file_id=$(dx upload /scratch/${bam_name} --brief --wait --destination /cwic/test/)
  dx-reload-project
  md5sum_local=($(md5sum /scratch/${bam_name}))
  md5sum_uploaded=($(md5sum "/project/$proj/cwic/test/$bam_name"))
  if [ $md5sum_local != $md5sum_uploaded ]; then exit 1; fi
  dx rm $file_id
done
"""

        bash_script = bash_script.replace("PROJECT_PLACEHOLDER", PROJECT_NAME)
        input_args = {
            "cmd": bash_script
        }
        job = self.applet_dx.run(
            input_args,
            folder=TEST_FOLDER,
            project=DX_CWIC_PROJECT_ID,
            name=self.applet_basename
        )
        print("Waiting for the job {j_id} to complete".format(j_id=job.get_id()))
        job.wait_on_done()

    def test_run_sub_without_user_dx_token(self):
        """Test that dx-cwic-sub exits with an error if user dx token
        is not provided"""
        input_args = {
            "cmd": "dx-cwic-sub 'ls -l /project'"
        }
        job = self.applet_dx.run(
            input_args,
            folder=TEST_FOLDER,
            project=DX_CWIC_PROJECT_ID,
            name=self.applet_basename
        )
        TU.check_job_is_unsuccessful(job)

    def test_run_credentials_not_mounted(self):
        """Test that credentials file is not bind mounted into the Docker
        container if it is not provided"""
        input_args = {
            "cmd": 'if [ -f "/home/dnanexus/credentials" || -d "/home/dnanexus/credentials" ]; then exit 1; fi'
        }
        job = self.applet_dx.run(
            input_args,
            folder=TEST_FOLDER,
            project=DX_CWIC_PROJECT_ID,
            name=self.applet_basename
        )
        print("Waiting for the job {j_id} to complete".format(j_id=job.get_id()))
        job.wait_on_done()


if __name__ == '__main__':
    unittest.main()
