import dxpy


class test_utils():
    @staticmethod
    def check_if_exists_and_delete(file_name: str, project_id: str, folder: str):
        list_folder = dxpy.DXProject(project_id).list_folder(folder, describe={"fields": {"id": True, "name": True}})
        file_names = [i["describe"]["name"] for i in list_folder["objects"]]
        assert file_name in file_names

        # Clean up: get the ID of the created file and remove it
        f_ids = [f["describe"]["id"] for f in list_folder["objects"] if f["describe"]["name"] == file_name and f["describe"]["id"].startswith("file")]
        if f_ids:
            dxpy.api.container_remove_objects(
                project_id, {"objects": f_ids}
            )

    @staticmethod
    def check_job_is_unsuccessful(job):
        try:
            job.wait_on_done()
            # if job continued, fail this test
            raise Exception("Job should have failed with DXJobFailureError")
        except dxpy.exceptions.DXJobFailureError:
            failure_msg = job.describe()["failureMessage"]
            assert "Error" in failure_msg
