'''
Readme Development Metrics With waka time progress
'''
import re
import os
import base64
import requests
from github import Github, GithubException, InputGitAuthor
import datetime
import traceback
from urllib.parse import quote
import json

from dotenv import load_dotenv

load_dotenv()

START_COMMENT = '<!--START_SECTION:waka-->'
END_COMMENT = '<!--END_SECTION:waka-->'
listReg = f"{START_COMMENT}[\\s\\S]+{END_COMMENT}"

waka_key = os.getenv('INPUT_WAKATIME_API_KEY')
ghtoken = os.getenv('INPUT_GH_TOKEN')


# wakatime stt
show_waka_stats = 'y'
showOs = os.getenv('INPUT_SHOW_OS')
showLanguage = os.getenv('INPUT_SHOW_LANGUAGE')
showTimeZone = os.getenv('INPUT_SHOW_TIMEZONE')
showEditors = os.getenv('INPUT_SHOW_EDITORS')
show_total_code_time = os.getenv('INPUT_SHOW_TOTAL_CODE_TIME')

# Etc
locale = os.getenv('INPUT_LOCALE')
show_updated_date = os.getenv('INPUT_SHOW_UPDATED_DATE')
commit_by_me = os.getenv('INPUT_COMMIT_BY_ME')
commit_message = os.getenv('INPUT_COMMIT_MESSAGE')
symbol_version = os.getenv('INPUT_SYMBOL_VERSION').strip()
updated_date_format = os.getenv('INPUT_UPDATED_DATE_FORMAT')


truthy = ['true', '1', 't', 'y', 'yes']


def run_query(query):
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))


def make_graph(percent: float):
    '''Make progress graph from API graph'''
    if (symbol_version == '1'): # version 1
        done_block = '█'
        empty_block = '░'
    elif (symbol_version == '2'): #version 2
        done_block = '⣿'
        empty_block = '⣀'
    elif (symbol_version == '3'): # version 3
        done_block = '⬛'
        empty_block = '⬜'
    else:
        done_block = '█' #default is version 1
        empty_block = '░'

    pc_rnd = round(percent)
    return f"{done_block * int(pc_rnd / 4)}{empty_block * int(25 - int(pc_rnd / 4))}"


def make_list(data: list):
    '''Make List'''
    data_list = []
    for l in data[:5]:
        ln = len(l['name'])
        ln_text = len(l['text'])
        op = f"{l['name'][:25]}{' ' * (25 - ln)}{l['text']}{' ' * (20 - ln_text)}{make_graph(l['percent'])}   {l['percent']}%"
        data_list.append(op)
    return ' \n'.join(data_list)

def get_waka_time_stats():
    stats = ''
    request = requests.get(
        f"https://wakatime.com/api/v1/users/current/stats/last_7_days?api_key={waka_key}")
    no_activity = translate["No Activity Tracked This Week"]

    if request.status_code == 401:
        print("Error With WAKA time API returned " + str(request.status_code) + " Response " + str(request.json()))
    else:
        empty = True
        data = request.json()

        stats += '📊 **' + "Activity History for the Last 7 Days" + '** \n\n'
        stats += '```text\n'
        if showTimeZone.lower() in truthy:
            empty = False
            tzone = data['data']['timezone']
            stats = stats + '⌚︎ ' + translate['Timezone'] + ': ' + tzone + '\n\n'

        if showLanguage.lower() in truthy:
            empty = False
            if len(data['data']['languages']) == 0:
                lang_list = no_activity
            else:
                lang_list = make_list(data['data']['languages'])
            stats = stats + '💬 ' + translate['Languages'] + ': \n' + lang_list + '\n\n'

        if showEditors.lower() in truthy:
            empty = False
            if len(data['data']['editors']) == 0:
                edit_list = no_activity
            else:
                edit_list = make_list(data['data']['editors'])
            stats = stats + '🔥 ' + translate['Editors'] + ': \n' + edit_list + '\n\n'


        if showOs.lower() in truthy:
            empty = False
            if len(data['data']['operating_systems']) == 0:
                os_list = no_activity
            else:
                os_list = make_list(data['data']['operating_systems'])
            stats = stats + '💻 ' + translate['operating system'] + ': \n' + os_list + '\n\n'

        stats += '```\n\n'
        if empty:
            return ""
    return stats

def get_stats():
    '''Gets API data and returns markdown progress'''

    stats = ''

    if show_total_code_time.lower() in truthy:
        request = requests.get(
            f"https://wakatime.com/api/v1/users/current/all_time_since_today?api_key={waka_key}")
        if request.status_code == 401:
            print("Error With WAKA time API returned " + str(request.status_code) + " Response " + str(request.json()))
        elif "text" not in request.json()["data"]:
            print("User stats are calculating. Try again later.")
        else:
            data = request.json()
            stats += '![Code Time](http://img.shields.io/badge/' + quote(
                str("Code Time")) + '-' + quote(str(
                data['data']['text'])) + '-blue)\n\n'

    if show_waka_stats.lower() in truthy:
        stats += get_waka_time_stats()


    if show_updated_date.lower() in truthy:
        now = datetime.datetime.utcnow()
        d1 = now.strftime(updated_date_format)
        stats = stats + "\n Last Updated on " + d1 + " UTC"

    return stats


# def star_me():
# requests.put("https://api.github.com/user/starred/anmol098/waka-readme-stats", headers=headers)


def decode_readme(data: str):
    '''Decode the contents of old readme'''
    decoded_bytes = base64.b64decode(data)
    return str(decoded_bytes, 'utf-8')


def generate_new_readme(stats: str, readme: str):
    '''Generate a new Readme.md'''
    stats_in_readme = f"{START_COMMENT}\n{stats}\n{END_COMMENT}"
    return re.sub(listReg, stats_in_readme, readme)


if __name__ == '__main__':
    try:
        start_time = datetime.datetime.now().timestamp() * 1000
        if ghtoken is None:
            raise Exception('Token not available')
        g = Github(ghtoken)
        headers = {"Authorization": "Bearer " + ghtoken}
        username = "tkxkd0159"
        email = "41176085+tkxkd0159@users.noreply.github.com"
        print("Username " + username)
        repo = g.get_repo(f"{username}/{username}")
        contents = repo.get_readme()
        try:
            with open(os.path.join(os.path.dirname(__file__), 'translation.json'), encoding='utf-8') as config_file:
                data = json.load(config_file)
            translate = data[locale]
        except Exception as e:
            print("Cannot find the Locale choosing default to english")
            translate = data['en']
        waka_stats = get_stats()
        # star_me()
        rdmd = decode_readme(contents.content)
        new_readme = generate_new_readme(stats=waka_stats, readme=rdmd)
        if commit_by_me.lower() in truthy:
            committer = InputGitAuthor(username, email)
        else:
            committer = InputGitAuthor('readme-bot', '41898282+github-actions[bot]@users.noreply.github.com')
        if new_readme != rdmd:
            try:
                repo.update_file(path=contents.path, message=commit_message,
                                 content=new_readme, sha=contents.sha, branch='master',
                                 committer=committer)
            except:
                repo.update_file(path=contents.path, message=commit_message,
                                 content=new_readme, sha=contents.sha, branch='main',
                                 committer=committer)
            print("Readme updated")
        end_time = datetime.datetime.now().timestamp() * 1000
        print("Program processed in {} miliseconds.".format(round(end_time - start_time, 0)))
    except Exception as e:
        traceback.print_exc()
        print("Exception Occurred " + str(e))
