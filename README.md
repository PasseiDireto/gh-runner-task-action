# GitHub Runner ECS Task Action

This Action to runs a given ECS task definition that provides a [Self Hosted GitHub Action Runner](https://docs.github.com/en/free-pro-team@latest/actions/hosting-your-own-runners/about-self-hosted-runners). The idea is to have a self hosted runner ready for execute the following jobs in the workflow.

This was intended to work with this [self hosted instance](https://github.com/PasseiDireto/gh-runner) on a EC2/ECS cluster, using [this stack/task definition](https://github.com/PasseiDireto/gh-runner-ecs-ec2-stack). However, we believe this pattern is very common and can be used with similar approaches, given a custom task definition and ECS cluster. Further details on motivation, architecture and next steps are displayed on this article.


## Usage

Every workflow using this action is composed by at least to jobs: a `pre-job` that starts up the runner and a `actual-job` that will run the actual workload.

To run this job sided with [configure-aws-credentials](https://github.com/aws-actions/configure-aws-credentials) and basic config:

```yaml

on:
  push:
    branches: [main]
name: Run dummy workflow
jobs:
  pre-job:
    runs-on: ubuntu-latest
    steps:
    - name: Configure AWS Credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_KEY }}
        aws-region: ${{ secrets.AWS_DEFAULT_REGION }}
    - name: Provide a self hosted to execute this job
      uses: PasseiDireto/gh-runner-task-action@main
      with:
        github_pat: ${{ secrets.SPECIAL_ACCESS_TOKEN }}
        task_definition: 'my-task-def'
        cluster: 'my-ecs-cluster'
  actual-job:
     runs-on: self-hosted
     needs: pre-job
     steps:
       - run: python --version
```

Note that the second job has some particular tags: `runs-on` is set to `self-hosted`, while the `needs: pre-job` forces GitHub finish the first job successfully before starting the `actual-job`. If you don't want to use the official `configure-aws-credentials` action, you can also set the needed AWS env variables on the same step:

```yaml
jobs:
  pre-job:
    runs-on: ubuntu-latest
    steps:
    - name: Provide a self hosted to execute this job
      uses: PasseiDireto/gh-runner-task-action@main
      env:
        AWS_ACCESS_ID: ${{ secrets.AWS_ACCESS_ID }}
        AWS_SECRET_KEY: ${{ secrets.AWS_SECRET_KEY }}
        AWS_DEFAULT_REGION: ${{ secrets.AWS_REGION }}
      with:
        github_pat: ${{ secrets.SPECIAL_ACCESS_TOKEN }}
        task_definition: 'my-task-def'
        cluster: 'my-ecs-cluster'
```

The [configure-aws-credentials](https://github.com/aws-actions/configure-aws-credentials) approach is a bit longer, but has some advantages of dealing with some edge cases, setting up more environment variables and working with the `assumeRole` feature.

Be aware that the `github_pat` can't be the default `secrets.GITHUB_TOKEN`, as it does not have enough permissions to register a new runner. More details are [provided here](https://github.com/PasseiDireto/gh-runner#personal-access-token-pat).

If you need custom configurations to be passed on `run_task`, you can have a json with the desired values. The params are basically the same of [boto3's run task](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.run_task). You can see how it works on [task-params-example.json](https://github.com/PasseiDireto/gh-runner-task-action/blob/main/task-params-example.json). **Be sure you checkout your code before if you are using this file**:

```yaml
- name: Provide a self hosted to execute this job
  uses: PasseiDireto/gh-runner-task-action@main
  with:
    github_pat: ${{ secrets.SPECIAL_ACCESS_TOKEN }}
    task_definition: 'gh-runner'
    cluster: 'gh-runner'
    task_params_file: './my-task-params-file.json' # the default name is 'task-params.json'
```

You can also choose not to wait for the task to be running. It can be useful to spare some CI/CD minutes, but you'll need another mechanism to be sure your [runner is available](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-lifecycle.html) before running the actual job. If no self-hosted runners are available when the job starts, you will face the `No runner matching the specified labels was found: self-hosted` error. Still, this option is useful for usecases where you have at least one long running executor registered at repository or organization level.

```yaml
- name: Provide a self hosted to execute this job
  uses: PasseiDireto/gh-runner-task-action@main
  with:
    github_pat: ${{ secrets.SPECIAL_ACCESS_TOKEN }}
    task_definition: 'gh-runner'
    cluster: 'gh-runner'
    wait: false
```

If you use [ephemeral runners](https://github.com/PasseiDireto/gh-runner), you will need to launch multiple tasks for to handle multiple jobs in the same workflow.
Whether they are sequential, parallel or defined by the [the matrix approach](https://docs.github.com/en/free-pro-team@latest/actions/reference/workflow-syntax-for-github-actions#jobsjob_idstrategymatrix),
 you can use the `count` parameter to ensure multiple tasks being launched at the same API call:

```yaml
jobs:
  pre-job:
    runs-on: ubuntu-latest
    steps:
    - name: Provide a self hosted to execute this job
      uses: PasseiDireto/gh-runner-task-action@main
      env:
        AWS_ACCESS_ID: ${{ secrets.AWS_ACCESS_ID }}
        AWS_SECRET_KEY: ${{ secrets.AWS_SECRET_KEY }}
        AWS_DEFAULT_REGION: ${{ secrets.AWS_REGION }}
      with:
        github_pat: ${{ secrets.SPECIAL_ACCESS_TOKEN }}
        task_definition: 'my-task-def'
        cluster: 'my-ecs-cluster'
        count: 3
  job1:
    runs-on: self-hosted
    needs: pre-job
    ...
  job2:
    runs-on: self-hosted
    needs: pre-job
    ...
  job3:
    runs-on: self-hosted
    needs: pre-job
    ...
```

## Approach
The underlying code is basically a [call to boto3's run task](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.run_task). Since this call does not wait the task to be running (only placed) we need to be pooling against [describe tasks](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.describe_tasks) if we want to wait a running task. The params you specify will be merged with our [task-params-template.json](https://github.com/PasseiDireto/gh-runner-task-action/blob/main/task-params-example.json), with precedence.

## Notes about waiting multiple tasks
When you use `wait: true` (default) with `count > 1`, note that the action will wait for **at least one task to be ready.**
It means you can have failures after that and the job you still be considered successful. However, if one failure is detected before
any ready states, the execution will result in an error. If you don't want this behavior, the recommended way of having multiple tasks launched is [the matrix approach](https://docs.github.com/en/free-pro-team@latest/actions/reference/workflow-syntax-for-github-actions#jobsjob_idstrategymatrix).
Then you can be sure all runners are ready before reaching the next step:

```yaml
jobs:
  pre-job:
    runs-on: ubuntu-latest
    strategy:
      matrix:
          instances: [a, b, c] # three tasks will be launched
    steps:
    - name: Provide a self hosted to execute this job
      uses: PasseiDireto/gh-runner-task-action@main
      env:
        AWS_ACCESS_ID: ${{ secrets.AWS_ACCESS_ID }}
        AWS_SECRET_KEY: ${{ secrets.AWS_SECRET_KEY }}
        AWS_DEFAULT_REGION: ${{ secrets.AWS_REGION }}
      with:
        github_pat: ${{ secrets.PD_BOT_GITHUB_ACCESS_TOKEN }}
        task_definition: 'my-task-def'
        cluster: 'my-ecs-cluster'
        wait: true # default
        count: 1 # default
```

This is the intended behavior because as of now, GitHub expects at least one registered runner to [queue the jobs](https://docs.github.com/en/free-pro-team@latest/actions/hosting-your-own-runners/about-self-hosted-runners#usage-limits) and avoid failing with the message `No runner matching the specified labels was found: self-hosted`.
It means that for most use cases waiting one runner to be available is enough, and the following jobs will wait for new runners.

## Available Input

All the accepted variables are described in the `action.yaml` file. This table offers a short summary:

| Name               | Default          | Required | Description                                                                        |
|--------------------|------------------|----------|------------------------------------------------------------------------------------|
| github_pat         | -                | yes      | GitHub Personal Access Token used in Runner Registration                           |
| task_definition    | gh-runner        | no       | The name of the task definition                                                    |
| cluster            | -                | yes      | The name of the ECS cluster where the task should be placed                        |
| count              | 1                | no       | Number of tasks that should be launched. Useful for matrix/parallel workflows      |
| wait               | true             | no       | Whether the action should wait until at least one the task is in state RUNNING before finishing |
| capacity_provider  | default          | no       | The name of the desired Capacity Provider (attached to this cluster)               |
| task_role_arn      | -                | no       | ARN of the role used to instantiate the task                                       |
| execution_role_arn | -                | no       | ARN of the role used during task execution                                         |
| task_params_file   | task-params.json | no       | JSON file (path) with extra configurations                                         |


## Contributing

PRs welcome! This action is a Docker container, so it is very easy run it locally. Be sure you have all the required inputs represented as envrionment variables. For instance you will need a `INPUT_GITHUB_PAT` to represent the input `github_pat` the action will actually pass. Note the `INPUT_` preffix and the camel case representation. Don't forget the [AWS credentials variables](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-environment-variables).

### Development guide

Clone the repository using Git:
```sh
git clone git@github.com:PasseiDireto/gh-runner-task-action.git
```

You can build the image as:

```sh
docker build -t gh-runner-task-action .
```

Have an [env file](https://docs.docker.com/engine/reference/commandline/run/#set-environment-variables--e---env---env-file) ready with all the variables you need, such as:

```sh
INPUT_CLUSTER=my-cluster
INPUT_TASK_DEFINITION=my-task-definition
INPUT_GITHUB_PAT=my-githubpat
INPUT_WAIT=true
INPUT_TASK_PARAMS_FILE=task-params-example.json
INPUT_CAPACITY_PROVIDER=default
GITHUB_JOB=this-job
GITHUB_REPOSITORY_OWNER=MyOrg
GITHUB_REPOSITORY=MyOrg/this-job

AWS_ACCESS_KEY_ID=my-secret-key-id
AWS_SECRET_ACCESS_KEY=my-secret-key
AWS_DEFAULT_REGION=us-east-1
```

You can name it `.env` and then then run it the freshly built image:

```sh
docker run --rm --env-file=.env gh-runner-task-action
```

### Before you commit

Be sure all the tests and all the checks are passing:
```sh
pip install -r requirements/all.txt
make # run all checks
make tests # run all tests

```
