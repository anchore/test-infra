#!/usr/bin/env python

import copy
import json
import logging
import time
import random
import subprocess
import sys

import cli_driver_config as config

from faker import Faker

cmd_prefix = "anchore-cli --json "

def assemble_command(context, args):
    user = " --u " + context["user"]
    password = " --p " + context["password"]
    api_url = " --url " + context["api_url"] + " "
    command = cmd_prefix + user + password + api_url + args
    return command

def fake_account_with_user():
    faker = Faker()
    account = {}
    account["account_name"] = faker.name().replace(" ", "")
    account["user"] = faker.user_name()
    account["email"] = faker.email()
    account["passw"] = faker.password()
    return account

def make_logger():
    logger = logging.getLogger("cli_driver")
    logger.setLevel(logging.DEBUG)
    filehandler = logging.FileHandler("cli_driver.log", "w")
    filehandler.setLevel(logging.DEBUG)
    streamhandler = logging.StreamHandler(sys.stdout)
    streamhandler.setLevel(logging.INFO)
    logformat = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    filehandler.setFormatter(logformat)
    streamhandler.setFormatter(logformat)
    logger.addHandler(streamhandler)
    logger.addHandler(filehandler)
    return logger

def log_explicit_failure(test_type, action, message):
    if test_type == "positive":
        logger.warn(action + " | failed (positive test) " + message)
        positive_tests["fail"].append("{0} - {1}".format(action, message))
    else:
        logger.warn(action + " | failed (negative (test) " + message)
        negative_tests["fail"].append("{0} - {1}".format(action, message))

def log_results_simple(desired_state, state, test_type, action, message):
    if state == desired_state:
        if test_type == "positive":
            logger.info(action + " | passed (positive test) " + message)
            positive_tests["pass"].append("{0} - {1}".format(action, message))
        else:
            logger.info(action + " | failed (negative (test) " + message)
            negative_tests["fail"].append("{0} - {1}".format(action, message))
    else:
        if test_type == "positive":
            logger.info(action + " | failed (positive test) " + message)
            positive_tests["fail"].append("{0} - {1}".format(action, message))
        else:
            logger.info(action + " | passed (negative test) " + message)
            negative_tests["pass"].append("{0} - {1}".format(action, message))

def log_results_summary():
    logger.info("==============================")
    logger.info("Test Summary")
    if positive_tests["pass"]:
        logger.info("Positive Tests Passed")
        for test in positive_tests["pass"]:
            logger.info("\t{0}".format(test))
    if positive_tests["fail"]:
        logger.info("Positive Tests Failed")
        for test in positive_tests["fail"]:
            logger.info("\t{0}".format(test))
    if negative_tests["pass"]:
        logger.info("Negative Tests Passed")
        for test in negative_tests["pass"]:
            logger.info("\t{0}".format(test))
    if negative_tests["fail"]:
        logger.info("Negative Tests Failed")
        for test in negative_tests["fail"]:
            logger.info("\t{0}".format(test))
    logger.info("{0} total positive tests passed".format(len(positive_tests["pass"])))
    logger.info("{0} total positive tests failed".format(len(positive_tests["fail"])))
    logger.info("{0} total negative tests passed".format(len(negative_tests["pass"])))
    logger.info("{0} total negative tests failed".format(len(negative_tests["fail"])))
    logger.info("==============================")

# Account commands
def account(context):
    """Invoke the account CLI subcommands."""
    logger.info("account | starting subcommands")
    faker = Faker()
    account_name = faker.name().replace(" ", "")
    account_email = faker.email()
    account_add(context, account_name, account_email)
    account_get(context, account_name)
    account_disable(context, account_name)
    account_enable(context, account_name)
    account_del(context, account_name, test_type="negative")
    account_disable(context, account_name)
    account_del(context, account_name)
    account_list(context)
    account_list(context, account_override=True, test_type="negative")
    context = copy.deepcopy(root_context)
    account_user(context)
    context = copy.deepcopy(root_context)
    account_whoami(context)
    logger.info("account | finished subcommands")

def account_add(context, name, email, test_type="positive", log=True):
    """Invoke the account add CLI subcommand."""
    if log:
        logger.info("account_add | starting")
    command = assemble_command(context, " account add --email {0} {1}".format(email, name))
    if log:
        logger.debug("account_add | running command {0}".format(command))
    try:
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        state = response_json["state"]
        if log:
            log_results_simple("enabled", state, test_type, "account_add", "account: {0}; email: {1}; state: {2}".format(name, email, state))
            logger.info("account_add | finished")
    except Exception as e:
        if log:
            log_explicit_failure(test_type, "account_add", "failed to add account {0}".format(name))
            logger.error("account_add | error calling anchore-cli: {0}".format(e))

def account_get(context, name, test_type="positive"):
    """Invoke the account get CLI subcommand."""
    logger.info("account_get | starting")
    command = assemble_command(context, " account get {0}".format(name))
    try:
        logger.debug("account_get | running command: {0}".format(command))
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        state = response_json["state"]
        log_results_simple("enabled", state, test_type, "account_get", "account: {0}; state: {1}".format(name, state))
        logger.info("account_get | finished")
    except Exception as e:
        log_explicit_failure(test_type, "account_get", "failed to get account {0}".format(name))
        logger.error("account_get | error calling anchore-cli: {0}".format(e))

def account_disable(context, name, test_type="positive"):
    """Invoke the account disable CLI subcommand."""
    logger.info("account_disable | starting")
    command = assemble_command(context, " account disable {0}".format(name))
    try:
        logger.debug("account_disable | running command: {0}".format(command))
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        state = response_json["state"]
        log_results_simple("disabled", state, test_type, "account_disable", "account: {0}; state: {1}".format(name, state))
        logger.info("account_disable | finished")
    except Exception as e:
        log_explicit_failure(test_type, "account_disable", "failed to disable account {0}".format(name))
        logger.error("account_disable | error calling anchore-cli: {0}".format(e))

def account_enable(context, name, test_type="positive"):
    """Invoke the account enable CLI subcommand."""
    logger.info("account_enable | starting")
    command = assemble_command(context, " account enable {0}".format(name))
    try:
        logger.debug("account_enable | running command: {0}".format(command))
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        state = response_json["state"]
        log_results_simple("enabled", state, test_type, "account_enable", "account: {0}; state: {1}".format(name, state))
        logger.info("account_enable | finished")
    except Exception as e:
        log_explicit_failure(test_type, "account_enable", "failed to enable account {0}".format(name))
        logger.error("account_enable | error calling anchore-cli: {0}".format(e))

def account_del(context, name, test_type="positive"):
    """Invoke the account del CLI subcommand."""
    logger.info("account_del | starting")
    command = assemble_command(context, " account del --dontask {0}".format(name))
    try:
        logger.debug("account_del | running command: {0}".format(command))
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        state = response_json["state"]
        log_results_simple("deleting", state, test_type, "account_del", "account: {0}; state: {1}".format(name, state))
        logger.info("account_del | finished")
    except Exception as e:
        if isinstance(e, subprocess.CalledProcessError):
            response_json = json.loads(e.stdout)
            if response_json["message"] == "Invalid account state change requested. Cannot go from state enabled to state deleting":
                log_results_simple("deleting", "enabled", test_type, "account_del", "could not delete account: {0}".format(name))
        else:
            log_explicit_failure(test_type, "account_del", "failed to delete account {0}".format(name))
            logger.error("account_del | error calling anchore-cli: {0}".format(e))

def account_list(context, account_override=False, test_type="positive"):
    """Invoke the account list CLI subcommand."""
    logger.info("account_list | starting")

    # make a non-admin user, and thus expect `account list` to fail
    # this implies that test_type is "negative"
    if account_override:
        acct = fake_account_with_user()
        account_add(context, acct["account_name"], acct["email"], test_type="positive", log=False)
        account_user_add(context, acct["account_name"], acct["user"], acct["passw"], test_type="positive", log=False)
        context["user"] = acct["user"]
        context["password"] = acct["passw"]

    command = assemble_command(context, " account list")

    try:
        logger.debug("account_list | running command: {0}".format(command))
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        number_accounts = len(response_json)
        log_results_simple("ok", "ok", test_type, "account_list", "{0} accounts found".format(number_accounts))
        logger.info("account_list | finished")
    except Exception as e:
        if isinstance(e, subprocess.CalledProcessError):
            response_json = json.loads(e.stdout)
            if account_override:
                if response_json == "Unauthorized" or response_json["httpcode"] == 403:
                    log_results_simple("ok", "notok", "negative", "account_list", "non-admin user could not list accounts")
                else:
                    log_explicit_failure(test_type, "account_list", "failed to list accounts")
                    logger.error("account_list | error calling anchore-cli: {0}".format(e))
        else:
            log_explicit_failure(test_type, "account_list", "failed to list accounts")
            logger.error("account_list | error calling anchore-cli: {0}".format(e))

def account_user(context, test_type="positive"):
    """Invoke the account user CLI subcommands."""
    logger.info("account_user | starting subcommands")
    account_user_list(context, test_type)
    context = copy.deepcopy(root_context)
    acct = fake_account_with_user()
    account_add(context, acct["account_name"], acct["email"], test_type)
    account_user_add(context, acct["account_name"], acct["user"], acct["passw"], test_type)
    account_user_del(context, test_type)
    account_user_get(context, test_type)
    account_user_setpassword(context, test_type)
    logger.info("account_user | finished subcommands")

def account_user_list(context, test_type):
    """Invoke the account user list CLI subcommand.

    We execute 4 cases:
    1. Default user list using admin (no --account)
    2. User list for an account without users using admin
    3. User list for an account with users using admin
    4. User list using a non-admin user

    Note: reset the context after calling this function
    ( context = copy.deepcopy(root_context) ).
    """
    logger.info("account_user_list | starting")
    command = assemble_command(context, " account user list")

    # case 1: default user list
    try:
        logger.debug("account_user_list | running command: {0}".format(command))
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        number_users = len(response_json)
        if number_users:
            log_results_simple("ok", "ok", test_type, "account_user_list", "{0} users found".format(number_users))
        else:
            # this is unlikely, as the command will fail if the admin user doesn't exist!
            log_results_simple("ok", "notok", "positive", "account_user_list", "no users found")
    except Exception as e:
        log_explicit_failure(test_type, "account_user_list", "failed list users w/admin")
        logger.error("account_user_list | error calling anchore-cli: {0}".format(e))

    # case 2: user list for account w/no users
    try:
        # set up - create an account with no users
        faker = Faker()
        account_name = faker.name().replace(" ", "")
        account_email = faker.email()
        account_add(context, account_name, account_email, log=False)
        command = assemble_command(context, " account user list --account {0}".format(account_name))
        logger.debug("account_user_list | running command: {0}".format(command))
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        number_users = len(response_json)
        if not number_users:
            # desired result
            log_results_simple("ok", "notok", "negative", "account_user_list", "no users found (good)")
        else:
            # there shouldn't be any users for this account, so this is a failure condition
            log_results_simple("ok", "notok", "positive", "account_user_list", "{0} users found".format(number_users))
    except Exception as e:
        log_explicit_failure(test_type, "account_user_list", "failed to list users w/admin for account w/no users")
        logger.error("account_user_list | error calling anchore-cli: {0}".format(e))

    # case 3: user list for account with users
    try:
        # set up - create an account with a user
        acct = fake_account_with_user()
        account_add(context, acct["account_name"], acct["email"], test_type="positive", log=False)
        account_user_add(context, acct["account_name"], acct["user"], acct["passw"], test_type="positive", log=False)

        command = assemble_command(context, " account user list --account {0}".format(acct["account_name"]))
        logger.debug("account_user_list | running command: {0}".format(command))
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        number_users = len(response_json)
        if number_users:
            log_results_simple("ok", "ok", "positive", "account_user_list", "{0} users found".format(number_users))
        else:
            log_results_simple("ok", "notok", "positive", "account_user_list", "no users found")
    except Exception as e:
        log_explicit_failure(test_type, "account_user_list", "failed to list users w/admin for account w/a user")
        logger.error("account_user_list | error calling anchore-cli: {0}".format(e))

    # case 4: list users in an account, using a non-admin user
    acct = fake_account_with_user()
    account_add(context, acct["account_name"], acct["email"], test_type="positive", log=False)
    account_user_add(context, acct["account_name"], acct["user"], acct["passw"], test_type="positive", log=False)
    context["user"] = acct["user"]
    context["password"] = acct["passw"]

    command = assemble_command(context, " account user list --account {0}".format(acct["account_name"]))

    try:
        logger.debug("account_user_list | running command: {0}".format(command))
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        number_users = len(response_json)
        # we expect this to throw an exception
        log_results_simple("ok", "ok", "negative", "account_user_list", "{0} users found - but should have thrown an exception".format(number_users))
    except Exception as e:
        if isinstance(e, subprocess.CalledProcessError):
            response_json = json.loads(e.stdout)
            if response_json == "Unauthorized" or response_json["httpcode"] == 403:
                log_results_simple("ok", "notok", "negative", "account_user_list", "Non-admin user could not list accounts (good)")
            else:
                logger.error("account_user_list | error calling anchore-cli: {0}".format(e))
        else:
            log_explicit_failure(test_type, "account_user_list", "failed to list users w/a non admin user")
            logger.error("account_user_list | error calling anchore-cli: {0}".format(e))
    logger.info("account_user_list | finished")

def account_user_add(context, account, username, userpass, test_type, log=True):
    """Invoke the account user add CLI subcommand."""
    if log:
        logger.info("account_user_add | starting")
    command = assemble_command(context, " account user add --account {0} {1} {2}".format(account, username, userpass))
    if log:
        logger.debug("account_user_add | running command {0}".format(command))
    try:
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        created = response_json["created_at"]
        user = response_json["username"]
        if log:
            logger.info("account_user_add | finished")
            if created and user:
                log_results_simple("ok", "ok", "positive", "account_user_add", "user: {0} added at {1}".format(user, created))
            else:
                log_results_simple("ok", "notok", "positive", "account_user_add", "user not added; json response: {0}".format(response_json))
    except Exception as e:
        if log:
            log_explicit_failure(test_type, "account_user_add", "failed to add user {0} to account {1}".format(username, account))
            logger.error("account_user_add | error calling anchore-cli: {0}".format(e))

def account_user_del(context, test_type):
    """Invoke the account user add CLI subcommand."""
    logger.info("account_user_del | starting")
    acct = fake_account_with_user()
    account_add(context, acct["account_name"], acct["email"], test_type="positive", log=False)
    account_user_add(context, acct["account_name"], acct["user"], acct["passw"], test_type="positive", log=False)
    command = assemble_command(context, " account user del --account {0} {1}".format(acct["account_name"], acct["user"]))
    logger.debug("account_user_del | running command {0}".format(command))
    try:
        # as long as this doesn't throw an exception or return 4xx, we're ok
        subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        log_results_simple("ok", "ok", "positive", "account_user_del", "user {0} deleted from account {1}".format(acct["user"], acct["account_name"]))
        logger.info("account_user_del | finished")
    except Exception as e:
        log_explicit_failure(test_type, "account_user_del", "failed to del user {0}".format(acct["user"]))
        logger.error("account_user_del | error calling anchore-cli: {0}".format(e))

def account_user_get(context, test_type):
    """Invoke the account user get CLI subcommand."""
    logger.info("account_user_get | starting")
    acct = fake_account_with_user()
    account_add(context, acct["account_name"], acct["email"], test_type="positive", log=False)
    account_user_add(context, acct["account_name"], acct["user"], acct["passw"], test_type="positive", log=False)
    command = assemble_command(context, " account user get --account {0} {1}".format(acct["account_name"], acct["user"]))
    logger.debug("account_user_get | running command {0}".format(command))
    try:
        # as long as this doesn't throw an exception or return 4xx, we're ok
        subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        log_results_simple("ok", "ok", "positive", "account_user_get", "got user {0} from account {1}".format(acct["user"], acct["account_name"]))
        logger.info("account_user_get | finished")
    except Exception as e:
        log_explicit_failure(test_type, "account_user_get", "failed to get user {0}".format(acct["user"]))
        logger.error("account_user_get | error calling anchore-cli: {0}".format(e))


def account_user_setpassword(context, test_type):
    """Invoke the account user setpassword CLI subcommand."""
    logger.info("account_user_setpassword | starting")
    acct = fake_account_with_user()
    account_add(context, acct["account_name"], acct["email"], test_type="positive", log=False)
    account_user_add(context, acct["account_name"], acct["user"], acct["passw"], test_type="positive", log=False)
    command = assemble_command(context, " account user setpassword --account {0} --username {1} {2}".format(acct["account_name"], acct["user"], acct["passw"]))
    logger.debug("account_user_setpassword | running command {0}".format(command))
    try:
        # as long as this doesn't throw an exception or return 4xx, we're ok
        subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        log_results_simple("ok", "ok", "positive", "account_user_setpassword", "set password of user {0} from account {1}".format(acct["user"], acct["account_name"]))
        logger.info("account_user_setpassword | finished")
    except Exception as e:
        log_explicit_failure(test_type, "account_user_setpassword", "failed to set password of user {0}".format(acct["user"]))
        logger.error("account_user_setpassword | error calling anchore-cli: {0}".format(e))
# /Account user subcommands

def account_whoami(context, test_type="positive"):
    """Invoke the account whoami CLI subcommand."""
    logger.info("account_whoami | starting")
    acct = fake_account_with_user()
    account_add(context, acct["account_name"], acct["email"], test_type="positive", log=False)
    account_user_add(context, acct["account_name"], acct["user"], acct["passw"], test_type="positive", log=False)
    command = assemble_command(context, " account whoami")
    logger.debug("account_whoami | running command {0}".format(command))
    try:
        # as long as this doesn't throw an exception or return 4xx, we're ok
        subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        log_results_simple("ok", "ok", "positive", "account_whoami", "account whoami called successfully")
        logger.info("account_whoami | finished")
    except Exception as e:
        log_explicit_failure(test_type, "account_whoami", "failed to call account whoami")
        logger.error("account_whoami | error calling anchore-cli: {0}".format(e))
# /Account commands

# Analysis archive
def analysis_archive(context):
    """Invoke the analysis_archive CLI subcommands."""
    logger.info("analysis-archive| starting subcommands [fake]")
    analysis_archive_images()
    analysis_archive_rules()

def analysis_archive_images():
    analysis_archive_images_add()
    analysis_archive_images_del()
    analysis_archive_images_get()
    analysis_archive_images_list()
    analysis_archive_images_restore()

def analysis_archive_images_add():
    pass

def analysis_archive_images_del():
    pass

def analysis_archive_images_get():
    pass

def analysis_archive_images_list():
    pass

def analysis_archive_images_restore():
    pass

def analysis_archive_rules():
    analysis_archive_rules_add()
    analysis_archive_rules_del()
    analysis_archive_rules_get()
    analysis_archive_rules_list()

def analysis_archive_rules_add():
    pass

def analysis_archive_rules_del():
    pass

def analysis_archive_rules_get():
    pass

def analysis_archive_rules_list():
    pass
# /Analysis archive

# Evaluate
def evaluate(context):
    """Invoke the evaluate CLI subcommands."""
    logger.info("evaluate | starting subcommands [fake]")
    evaluate_check()

def evaluate_check():
    pass
# /Evaluate

# Event
def event(context):
    """Invoke the event CLI subcommands."""
    logger.info("event | starting subcommands [fake]")
    event_delete()
    event_get()
    event_list()

def event_delete():
    pass

def event_get():
    pass

def event_list():
    pass
# /Event

# Image
def image(context):
    """Invoke the image CLI subcommands."""
    logger.info("image | starting subcommands")
    image_add(context)
    image_wait(context)
    image_get(context)
    image_content(context)
    image_metadata(context)
    image_list(context)
    image_vuln(context)
    image_del(context, test_type="negative")
    image_del(context, force=True)
    #image_import(context)

def image_add(context, test_type="positive"):
    """Invoke the image add CLI subcommand."""
    logger.info("image_add | starting")
    for image in config.test_images:
        command = assemble_command(context, " image add {0}".format(image))
        try:
            logger.debug("image_add | running command {0}".format(command))
            completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
            response_json = json.loads(completed_proc.stdout)
            image_status = response_json[0]["image_status"]
            logger.info("image_add | added image {0}; status: {1}".format(image, image_status))
            log_results_simple(image_status, "active", test_type, "image_add", "added image {0}".format(image))
        except Exception as e:
            log_explicit_failure(test_type, "image_add", "failed to add image {0}".format(image))
            logger.error("image_add | error calling anchore-cli: {0}".format(e))
    logger.info("image_add | finished")

def image_content(context, test_type="positive"):
    """Invoke the image content CLI subcommand."""
    logger.info("image_content | starting")

    # Wait for the image to be available
    image = random.choice(config.test_images)
    command = assemble_command(context, " image wait {0}".format(image))
    try:
        logger.debug("image_content | running command {0}".format(command))
        logger.info("image_content | waiting for image {0} to be available".format(image))
        subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
    except Exception as e:
        logger.debug("image_content | something went a bit wrong: {0}".format(e))
        logger.info("image_content | call failed; returning. Exception: {0}".format(e))
        return

    # Get the content types for our random image
    try:

        command = assemble_command(context, " image content {0}".format(image))
        logger.debug("image_content | running command {0}".format(command))
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        if not response_json:
            log_explicit_failure(test_type, "image_content", "no content types for image {0}".format(image))
            return

        logger.info("image_content | found these content types for image {0}: {1}".format(image, response_json))

        for content in response_json:
            command = assemble_command(context, " image content {0} {1}".format(image, content))
            logger.debug("image_content | running command {0}".format(command))
            completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
            response_json = json.loads(completed_proc.stdout)
            content_length = len(response_json["content"])
            logger.info("image_content | found {0} of content type {1} in image {2}".format(content_length, content, image))

    except Exception as e:
        logger.debug("image_content | something went a bit wrong: {0}".format(e))
        logger.info("image_content | call failed; returning. Exception: {0}".format(e))
        return

    log_results_simple("ok", "ok", test_type, "image_content", "content types tested successfully")
    logger.info("image_content | finished")

def image_del(context, force=False, test_type="positive"):
    """Invoke the image del CLI subcommand."""
    logger.info("image_del | starting")

    image = random.choice(config.test_images)
    command = assemble_command(context, " image del {0}".format(image))
    if force:
        command = assemble_command(context, " image del --force {0}".format(image))

    # Wait for the image to be available
    wait_command = assemble_command(context, " image wait {0}".format(image))
    try:
        logger.debug("image_del | running command {0}".format(wait_command))
        logger.info("image_del | waiting for image {0} to be available".format(image))
        subprocess.run(wait_command.split(), check=True, stdout=subprocess.PIPE)
    except Exception as e:
        logger.debug("image_del | something went a bit wrong: {0}".format(e))
        logger.info("image_del | call failed; returning. Exception: {0}".format(e))
        return

    try:
        logger.debug("image_del | running command {0}".format(command))
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        status = response_json["status"]
        log_results_simple("deleting", status, test_type, "image_del", "delete image {0}".format(image))
        logger.info("image_del | finished")
    except Exception as e:
        if isinstance(e, subprocess.CalledProcessError):
            response_json = json.loads(e.stdout)
            if response_json["message"] == "cannot delete image that is the latest of its tags, and has active subscription":
                if force:
                    log_explicit_failure(test_type, "image_del", "could not delete image: {0}".format(image))
                else:
                    # assumes negative test... might not be a good idea
                    log_results_simple("ok", "notok", test_type, "image_del", "could not delete image without forcing: {0} (good)".format(image))
        else:
            log_explicit_failure(test_type, "image_del", "failed to delete image")
            logger.error("image_del | error calling anchore-cli: {0}".format(e))

# Note, you don't have to wait for the image to be available to call `image get`
def image_get(context, test_type="positive"):
    """Invoke the image get CLI subcommand."""
    logger.info("image_get | starting")
    for image in config.test_images:
        command = assemble_command(context, " image get {0}".format(image))
        try:
            logger.debug("image_get | running command {0}".format(command))
            subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
            # as long as this doesn't throw an exception or return 4xx, we're ok
            log_results_simple("ok", "ok", test_type, "image_get", "got image {0}".format(image))
        except Exception as e:
            log_explicit_failure(test_type, "image_get", "failed to get image {0}".format(image))
            logger.error("image_get | error calling anchore-cli: {0}".format(e))
    logger.info("image_get | finished")

def image_import(context):
    pass

def image_list(context, test_type="positive"):
    """Invoke the image list CLI subcommand."""
    logger.info("image_list | starting")
    command = assemble_command(context, " image list")

    try:
        logger.debug("image_list | running command: {0}".format(command))
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        number_images = len(response_json)
        # as long as this doesn't throw an exception or return 4xx, we're ok
        log_results_simple("ok", "ok", test_type, "image_list", "{0} images found".format(number_images))
        logger.info("image_list | finished")
    except Exception as e:
        log_explicit_failure(test_type, "image_list", "failed to list images")
        logger.error("image_list | error calling anchore-cli: {0}".format(e))

def image_metadata(context, test_type="positive"):
    """Invoke the image metadata CLI subcommand."""
    logger.info("image_metadata | starting")

    image = random.choice(config.test_images)
    command = assemble_command(context, " image metadata {0}".format(image))

    # Wait for the image to be available
    wait_command = assemble_command(context, " image wait {0}".format(image))
    try:
        logger.debug("image_metadata | running command {0}".format(wait_command))
        logger.info("image_metadata | waiting for image {0} to be available".format(image))
        subprocess.run(wait_command.split(), check=True, stdout=subprocess.PIPE)
    except Exception as e:
        logger.debug("image_metadata | something went a bit wrong: {0}".format(e))
        logger.info("image_metadata | call failed; returning. Exception: {0}".format(e))
        return

    # First, we invoke the command without a metadata type; we expect to get back
    # a JSON blob w/manifest, docker_history, and dockerfile metadata types.
    # Then, we call for each of those types of metadata from the image.
    try:
        logger.debug("image_metadata | running command: {0}".format(command))
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        failed = False
        for key in config.metadata_types:
            if not key in response_json:
                failed = True
                log_explicit_failure(test_type, "image_metadata", "{0} metadata type was not found for {1}".format(key, image))
            subcommand = assemble_command(context, " image metadata {0} {1}".format(image, key))
            sub_proc = subprocess.run(subcommand.split(), check=True, stdout=subprocess.PIPE)
            sub_json = json.loads(sub_proc.stdout)
            m_type = sub_json["metadata_type"]
            if not m_type or m_type != key:
                failed = True
                log_explicit_failure(test_type, "image_metadata", "{0} was not expected metadata type {1} for image {2}".format(m_type, key, image))
        if not failed:
            log_results_simple("ok", "ok", test_type, "image_metadata", "all expected metadata keys found")
        logger.info("image_metadata | finished")
    except Exception as e:
        log_explicit_failure(test_type, "image_metadata", "failed to get image metadata for {0}".format(image))
        logger.error("image_metadata | error calling anchore-cli: {0}".format(e))


def image_vuln(context, test_type="positive"):
    """Invoke the image vuln CLI subcommand."""
    logger.info("image_vuln | starting")

    image = random.choice(config.test_images)

    # Wait for the image to be available
    wait_command = assemble_command(context, " image wait {0}".format(image))
    try:
        logger.debug("image_vuln | running command {0}".format(wait_command))
        logger.info("image_vuln | waiting for image {0} to be available".format(image))
        subprocess.run(wait_command.split(), check=True, stdout=subprocess.PIPE)
    except Exception as e:
        logger.debug("image_vuln | something went a bit wrong: {0}".format(e))
        logger.info("image_vuln | call failed; returning. Exception: {0}".format(e))
        return

    try:
        failed = False
        for key in config.vulnerability_types:
            command = assemble_command(context, " image vuln {0} {1}".format(image, key))
            logger.debug("image_vuln | running command: {0}".format(command))
            completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
            response_json = json.loads(completed_proc.stdout)
            vuln_type = response_json["vulnerability_type"]
            num_vulns = len(response_json["vulnerabilities"])
            if not vuln_type or vuln_type != key:
                failed = True
                log_explicit_failure(test_type, "image_vuln", "{0} was not expected vuln type {1} for image {2}".format(vuln_type, key, image))
            else:
                log_results_simple("ok", "ok", test_type, "image_vuln", "found {0} vuln of type {1} for image {2}".format(num_vulns, key, image))
        if not failed:
            log_results_simple("ok", "ok", test_type, "image_vuln", "all expected metadata keys found")
        logger.info("image_vuln | finished")
    except Exception as e:
        log_explicit_failure(test_type, "image_vuln", "failed to get vuln data for image {0}".format(image))
        logger.error("image_vuln | error calling anchore-cli: {0}".format(e))

def image_wait(context, timeout=-1, interval=5, test_type="positive"):
    logger.info("image_vuln | starting")
    image = random.choice(config.test_images)
    command = assemble_command(context, " image wait {0} --timeout {1} --interval {2}".format(image, timeout, interval))

    # Wait for the image to be available
    wait_command = assemble_command(context, " image wait {0}".format(image))
    try:
        logger.debug("image_wait | running command {0}".format(wait_command))
        logger.info("image_wait | waiting for image {0} to be available".format(image))
        subprocess.run(wait_command.split(), check=True, stdout=subprocess.PIPE)
    except Exception as e:
        logger.debug("image_wait | something went a bit wrong: {0}".format(e))
        logger.info("image_wait | call failed; returning. Exception: {0}".format(e))
        return

    try:
        logger.debug("image_wait | running command {0}".format(command))
        completed_proc = subprocess.run(command.split(), check=True, stdout=subprocess.PIPE)
        response_json = json.loads(completed_proc.stdout)
        status = response_json[0]["analysis_status"]
        log_results_simple("analyzed", status, test_type, "image_wait", "waited for image {0}".format(image))
        logger.info("image_wait | finished")
    except Exception as e:
        logger.debug("image_wait | something went a bit wrong: {0}".format(e))
        logger.info("image_wait | call failed; returning. Exception: {0}".format(e))

# /Image

# Policy
def policy(context):
    """Invoke the policy CLI subcommands."""
    logger.info("policy | starting subcommands [fake]")
    policy_activate()
    policy_add()
    policy_del()
    policy_describe()
    policy_get()
    policy_hub()
    policy_list()

def policy_activate():
    pass

def policy_add():
    pass

def policy_del():
    pass

def policy_describe():
    pass

def policy_get():
    pass

def policy_hub():
    policy_hub_get()
    policy_hub_install()
    policy_hub_list()

def policy_hub_get():
    pass

def policy_hub_install():
    pass

def policy_hub_list():
    pass

def policy_list():
    """Invoke the policy CLI subcommands."""
    logger.info("policy_activate | starting")
# /Policy

# Query
def query(context):
    """Invoke the query CLI command."""
    logger.info("query | starting subcommands [fake]")
# /Query

# Repo
def repo(context):
    """Invoke the repo CLI subcommands."""
    logger.info("repo | starting subcommands [fake]")
    repo_add()
    repo_del()
    repo_get()
    repo_list()
    repo_unwatch()
    repo_watch()

def repo_add():
    pass

def repo_del():
    pass

def repo_get():
    pass

def repo_list():
    pass

def repo_unwatch():
    pass

def repo_watch():
    pass
# /Repo

# Subscription
def subscription(context):
    """Invoke the subscription CLI subcommands."""
    logger.info("subscription | starting subcommands [fake]")
    subscription_activate()
    subscription_deactivate()
    subscription_list()

def subscription_activate():
    pass

def subscription_deactivate():
    pass

def subscription_list():
    pass
# /Subscription

# System
def system(context):
    """Invoke the system CLI subcommands."""
    logger.info("system | starting subcommands [fake]")
    system_del()
    system_errorcodes()
    system_feeds()
    system_status()
    system_wait()

def system_del():
    pass

def system_errorcodes():
    pass

def system_feeds():
    system_feeds_config()
    system_feeds_delete()
    system_feeds_list()
    system_feeds_sync()

def system_feeds_config():
    pass

def system_feeds_delete():
    pass

def system_feeds_list():
    pass

def system_feeds_sync():
    pass

def system_status():
    pass

def system_wait():
    pass
# /System

logger = make_logger()
positive_tests = { "pass": [], "fail": [] }
negative_tests = { "pass": [], "fail": [] }
root_context = dict()

def parse_config_and_run():

    root_context["user"] = config.default_admin_user
    root_context["password"] = config.default_admin_pass
    root_context["api_url"] = config.api_url
    context = copy.deepcopy(root_context)

    # Figure out which top level CLI command is being called, then call it
    command = sys.argv[1] if len(sys.argv) == 2 else "all"
    if command == "all":
        account(context)
        context = copy.deepcopy(root_context)
        image(context)
        analysis_archive(context)
        evaluate(context)
        event(context)
        policy(context)
        subscription(context)
        system(context)
    else:
        func = getattr(sys.modules[__name__], command)
        func(context)

    log_results_summary()

if __name__ == '__main__':
    parse_config_and_run()

