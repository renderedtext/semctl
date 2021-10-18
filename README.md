# Semaphore Controller command line tool (semctl)

Tooling which relies on Semaphore public API to make most common actions like
checking pipeline's status or triggering a promotion easy to do in jobs on Semaphore.

# Usage

1) Create secret that exposes API authorization token as API_TOKEN and attach it to desired jobs.
2) Include the script in your repository, e.g. save it in `.semaphore/semctl.py`
3) Add the following commands after `checkout` command in your jobs
```
chmod +x .semaphore/semctl.py
sudo mv .semaphore/semctl.py /usr/local/bin/semctl
```
4) Add following command to run the desired action `semctl {action} {flags} {inputs}`

# Specification

## `pipeline_status` action

**Description**:

  Fetches status of the pipeline via Semaphore HTTP API.
  The pipeline can be identified either by pipeline ID or by a combination of the path to the yaml file within the repository and the workflow ID.

**Inputs**:

 - pipeline_id - required if flag with `yaml_file_path` value is not given

**Flags**:
 | Flag                        | Explanation                                                                                                                                     |
 | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
 | -h                            | Show help                                                                                                                                       |
 | -f <yaml_file_path>|  Used only if pipeline_id is not given. Default: ".semaphore/semaphore.yml"                                 |
 | -w <workflow_id>   |  Used only if pipeline_id is not given. Default: value of SEMAPHORE_WORKFLOW_ID env var |

**Required preexisting environment variables**:

- `API_TOKEN` - holds personal API token used for authentication on Semaphore API
  We suggest creating a robot GitHub account, adding it only to necessary projects, and exposing its API token as this environment variable via Semaphore secret.

- `SEMAPHORE_ORGANIZATION_URL` - automatically exported in jobs on Semaphore, holds the URL of the organization under which the job is run.

- `SEMAPHORE_WORKFLOW_ID` - automatically exported in jobs on Semaphore, holds the id of the current workflow.

**Output**:

  - on `success`:
    string with a status of the pipeline which is one of the following:
    - `RUNNING`  - pipeline is still running
    - `PASSED`   - pipeline is finished and all its jobs have passed
    - `FAILED`   - pipeline failed due to some of its jobs failing
    - `STOPPED`  - pipeline was stopped while it was running
    - `CANCELED` - pipeline was canceled before it started running

  - on `fail`:
    error message with more details about the failure

**Example usage**:

  - `semctl pipeline_status <pipeline_id>` -
    Returns status of the pipeline with given id.

  - `semctl pipeline_status -f ".semaphore/deploy.yml"` -
    Returns status of the latest pipeline created based on yaml configuration in `semaphore/deploy.yml` in the workflow with the id from the `SEMAPHORE_WORKFLOW_ID` environment variable.

  - `semctl pipeline_status -f ".semaphore/deploy.yml" -w <workflow_id>` -
    Returns status of the latest pipeline created based on yaml configuration in `semaphore/deploy.yml` in the workflow with the given id.

## `promotion_status` action

**Description**:

  Fetches a status of the latest pipeline triggered via a promotion with a given name.  

**Inputs**:

 - promotion_name - required, name of the promotion in the parent pipeline's `promotions` block of yaml configuration file.

**Flags**:
 | Flag                     | Explanation                                                                                                                                           |
 | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
 | -h                         | Show help                                                                                                                                             |
 |  -p <pipeline_id>  |  Optional, pipeline_id of the parent pipeline. Default: value of SEMAPHORE_PIPELINE_ID env var |

**Required preexisting environment variables**:

- `API_TOKEN` - holds personal API token used for authentication on Semaphore API
  We suggest creating a robot GitHub account, adding it only to necessary projects, and exposing its API token as this environment variable via Semaphore secret.

- `SEMAPHORE_ORGANIZATION_URL` - automatically exported in jobs on Semaphore, holds the URL of the organization under which the job is run.

- `SEMAPHORE_PIPELINE_ID` - automatically exported in jobs on Semaphore, holds the id of the current pipeline.

**Output**:

  - on `success`:
    string with a status of the promotion triggered pipeline, one of the following:
    - `RUNNING`  - pipeline is still running
    - `PASSED`   - pipeline is finished and all its jobs have passed
    - `FAILED`   - pipeline failed due to some of its jobs failing
    - `STOPPED`  - pipeline was stopped while it was running
    - `CANCELED` - pipeline was canceled before it started running

  - on `fail`:
    error message with more details about the failure

**Example usage**:

  - `semctl promotion_status "Production deployment"` -
    Returns status of the pipeline that was started by triggering a `Production deployment` promotion of a parent pipeline with id from the `SEMAPHORE_PIPELINE_ID` environment variable.

  - `semctl promotion_status -p <pipeline_id> "Production deployment"` -
    Returns status of the pipeline that was started by triggering a `Production deployment` promotion of a parent pipeline with a given pipeline_id.


## `promote` action

**Description**:

  Triggers a promotion of a current pipeline with a given promotion name.
  After the promotion is successfully triggered it will wait (up to 20 seconds) until the pipeline for that promotion is started and return its pipeline_id.

**Inputs**:

 - promotion_name - required, name of the promotion in the parent pipeline's `promotions` block of yaml configuration file.

**Flags**:

 | Flag                     | Explanation                                                                                                                                                     |
 | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
 | -h                         | Show help                                                                                                                                                       |
 |  -p <pipeline_id>  |  Optional, pipeline_id of the parent pipeline. Default: value of SEMAPHORE_PIPELINE_ID env var           |
 |  -o                        |  Sets `override` value to `true` which allows promotions even if parent pipeline is still running or has failed |

**Required preexisting environment variables**:

- `API_TOKEN` - holds personal API token used for authentication on Semaphore API
  We suggest creating a robot GitHub account, adding it only to the necessary projects, and exposing its API token as this environment variable via Semaphore secret.

- `SEMAPHORE_ORGANIZATION_URL` - automatically exported in jobs on Semaphore, holds the URL of the organization under which the job is run.

- `SEMAPHORE_PIPELINE_ID` - automatically exported in jobs on Semaphore, holds the id of the current pipeline

**Output**:

  - on `success`:
    pipeline_id of the pipeline that was started via this promote action

  - on `fail`:
    error message with more details about the failure

**Example usage**:

  - `semctl promote "Production deployment"` -
    Triggers a `Production deployment` promotion of a pipeline with id from the `SEMAPHORE_PIPELINE_ID` environment variable.
    The promotion will be successfully triggered only if the parent pipeline has passed because the `override` flag is not given.

  - `semctl promote -o "Production deployment"` -
    Triggers a `Production deployment` promotion of a pipeline with id from the `SEMAPHORE_PIPELINE_ID` environment variable.
    The promotion will be triggered regardless of the status of the parent pipeline because the `override` flag is present.     

  - `semctl promote -p <pipeline_id> "Production deployment"` -
    Triggers a `Production deployment` promotion of a pipeline with the given id.
    The promotion will be successfully triggered only if the parent pipeline has passed because the `override` flag is not given.
