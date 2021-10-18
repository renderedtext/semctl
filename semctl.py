#!/usr/bin/env python2

import os, sys, argparse, urllib, urllib2, json, time, traceback, logging, math

def read_required_env_vars():
    token = os.environ.get('API_TOKEN')
    if not token:
        print("Error: Authorization token needs to be stored as API_TOKEN env var.")
        sys.exit(1)
    org_url = os.environ.get('SEMAPHORE_ORGANIZATION_URL')
    if not org_url:
        print("Error: Organization specifc url needs to be stored as SEMAPHORE_ORGANIZATION_URL env var.")
        sys.exit(1)
    return token, org_url

def do_get(url, token, entity_name):
    req = urllib2.Request(url)
    req.add_header('Authorization', 'Token ' + token)
    try:
       resp = urllib2.urlopen(req)
    except urllib2.HTTPError as err:
       if err.code == 404:
           print("Error: " + entity_name +" that matches given parameters was not found.")
           sys.exit(1)
       if err.code == 500:
           print("Error: Internal server error.")
           sys.exit(1)
       else:
           raise
    content = resp.read()
    response = json.loads(content)
    return response

def get_status(url, token):
    response = do_get(url, token, "Pipeline")

    if isinstance(response, list):
        if len(response) > 0:
            pipeline = response[0]
        else:
            print("Error: Pipeline that matches given parameters was not found.")
            sys.exit(1)
    else:
        pipeline = response["pipeline"]

    if pipeline["state"].upper() == 'DONE':
        status = pipeline["result"].upper()
    else:
        status = "RUNNING"
    print(status)

def pipeline_status(args):
    token, org_url = read_required_env_vars()

    if args.file_path or args.workflow_id:
        pipeline_file = args.file_path or '.semaphore/semaphore.yml'
        wf_id = args.workflow_id or os.environ.get('SEMAPHORE_WORKFLOW_ID')
        if not wf_id:
            print("Error: The workflow ID value can not be found.")
            sys.exit(1)

        url = org_url + '/api/v1alpha/pipelines?'
        url = url +'wf_id=' + wf_id + '&yml_file_path=' + pipeline_file
        get_status(url, token)

    elif args.pipeline_id:
        url = org_url + '/api/v1alpha/pipelines/' + args.pipeline_id
        get_status(url, token)

    else:
        print("Error: Either pipeline ID or workflow ID and pipeline file path need to be provided.")
        sys.exit(1)

def get_promotion(url, token, promotion_name):
    promotions = do_get(url, token, "Promotion")

    promotion = ""

    for element in promotions:
      if element["name"] == promotion_name and element["status"] == 'passed':
         promotion = element
         break

    if not promotion:
        print("Error: Promotion that matches given parameters was not found.")
        sys.exit(1)

    return promotion

def promotion_status(args):
    token, org_url = read_required_env_vars()

    ppl_id = args.parent_id or os.environ.get('SEMAPHORE_PIPELINE_ID')
    if not ppl_id:
        print("Error: The pipeline ID value can not be found.")
        sys.exit(1)

    url = org_url + '/api/v1alpha/promotions?' + 'pipeline_id=' + ppl_id
    promotion = get_promotion(url, token, args.promotion_name)

    status_url = org_url + '/api/v1alpha/pipelines/' + promotion["scheduled_pipeline_id"]
    get_status(status_url, token)

def trigger_promotion(url, token, ppl_id, args):
    dict = {'pipeline_id' : ppl_id, 'name' : args.promotion_name, 'override' : args.override}
    data = urllib.urlencode(dict)
    req = urllib2.Request(url, data)
    req.add_header('Authorization', 'Token ' + token)
    try:
       resp = urllib2.urlopen(req)
    except urllib2.HTTPError as err:
       if err.code == 404:
           print("Error: Promotion targer that matches given parameters was not found.")
           sys.exit(1)
       if err.code == 500:
           print("Error: Internal server error.")
           sys.exit(1)
       else:
           raise

def sleep_until_started(list_url, token, promotion_name, trriger_time):
    promotion = False
    deadline = time.time() + 20
    while deadline - time.time() > 0:
        time.sleep(2)
        try:
            promotions = do_get(list_url, token, "Promotion")
            for element in promotions:
              if (
                  element["name"] == promotion_name and
                  element["status"] == 'passed' and
                  element["triggered_at"]["seconds"] >= trriger_time
                  ):
                 promotion = element

            if promotion:
                return promotion["scheduled_pipeline_id"]
        except Exception as e:
            logging.error(traceback.format_exc())
            continue
    else:
        print("Error: Failed to verify the status of the promotion in the 20 seconds timeframe.")
        sys.exit(1)

def promote(args):
    token, org_url = read_required_env_vars()

    ppl_id = args.parent_id or os.environ.get('SEMAPHORE_PIPELINE_ID')
    if not ppl_id:
        print("Error: The pipeline ID value can not be found.")
        sys.exit(1)

    trriger_time = math.floor(time.time())

    url = org_url + '/api/v1alpha/promotions'
    trigger_promotion(url, token, ppl_id, args)

    list_url = org_url + '/api/v1alpha/promotions?' + 'pipeline_id=' + ppl_id
    scheduled_ppl_id = sleep_until_started(list_url, token, args.promotion_name, trriger_time)
    print(scheduled_ppl_id)

def main(argv):
    # create the top-level parser
    parser = argparse.ArgumentParser(prog='semctl')
    subparsers = parser.add_subparsers(title='available commands')

    # create the parser for the "pipeline_status" command
    desc_ppl_status = "Fetches status of the pipeline via Semaphore HTTP API.\n\n"
    desc_ppl_status += "The pipeline can be identified either by pipeline ID or\n"
    desc_ppl_status += "by a combination of the path to the yaml file within the\n"
    desc_ppl_status += "repository and the workflow ID."

    parser_ppl_st = subparsers.add_parser('pipeline_status', description=desc_ppl_status,
                    help='Get status of a pipeline', formatter_class=argparse.RawDescriptionHelpFormatter)

    help_id = 'ID of the pipeline, required unless combination of -f and -w flag values is provided'
    parser_ppl_st.add_argument('pipeline_id', nargs='?', default=False, help=help_id)

    help_f = 'Path to YAML file in repository, default: ".semaphore/semaphore.yml"'
    parser_ppl_st.add_argument('-f', dest='file_path', metavar='file_path', help=help_f)

    help_w = 'ID of the workflow, default: read from SEMAPHORE_WORKFLOW_ID env var'
    parser_ppl_st.add_argument('-w', dest='workflow_id', metavar='workflow_id', help=help_w)

    parser_ppl_st.set_defaults(func=pipeline_status)

    # create the parser for the "promotion_status" command
    desc_prom_status = "Fetches a status of the latest pipeline triggered via a promotion with a given name."

    parser_prom_st = subparsers.add_parser('promotion_status', description=desc_prom_status,
                                           help='Get status of a promoted pipeline')

    help_pn = "Name of the promotion in the parent pipeline's promotions block of the yaml configuration file"
    parser_prom_st.add_argument('promotion_name', default=False, help=help_pn)

    help_p = 'Id of the parent pipeline, default: read from SEMAPHORE_PIPELINE_ID env var'
    parser_prom_st.add_argument('-p', dest='parent_id', metavar='pipeline_id', help=help_p)

    parser_prom_st.set_defaults(func=promotion_status)

    # create the parser for the "promote" command
    desc_promote = "Triggers a promotion of a current pipeline with a given promotion name.\n\n"
    desc_promote += "After the promotion is successfully triggered it will wait (up to 15 seconds)\n"
    desc_promote += "until the pipeline for that promotion is started and return its pipeline_id."

    parser_promote = subparsers.add_parser('promote', description=desc_promote,
                    help='Trigger a promotion', formatter_class=argparse.RawDescriptionHelpFormatter)

    parser_promote.add_argument('promotion_name', default=False, help=help_pn)

    parser_promote.add_argument('-p', dest='parent_id', metavar='pipeline_id', help=help_p)

    help_o = "Sets override value to true which allows promotions even if parent pipeline is still running or has failed"
    parser_promote.add_argument('-o', dest='override', action='store_const', const='true', default='false', help=help_o)

    parser_promote.set_defaults(func=promote)

    # parse the args and call whatever function was selected
    args = parser.parse_args(argv)
    args.func(args)

if __name__ == "__main__":
   main(sys.argv[1:])
