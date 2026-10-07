import requests
from github import Github, Auth
from datetime import datetime
from os import getenv

saved_projects = []
download_count = []
g = Github(auth=Auth.Token(getenv('ACCESS_TOKEN')))


def get_github_downloads(user):
    counted_downloads = 0

    user = g.get_user(user)

    for repo in user.get_repos():
        try:
            repo_download_count = 0
            print(repo.name)

            for release in repo.get_releases():
                for asset in release.get_assets():
                    print('{}, {}'.format(repo.name, asset))

                    counted_downloads += asset.download_count
                    repo_download_count += asset.download_count

            saved_projects.append(
                [repo.name, repo.description, repo.stargazers_count, repo.url, repo_download_count, 'Github'])
            download_count.append(repo_download_count)
        except:
            ''

    return counted_downloads


def get_modrinth_downloads(user):
    counted_downloads = 0
    url = "https://api.modrinth.com/v2/user/{}/projects".format(user)
    response = requests.get(url).json()

    for mod in response:
        counted_downloads += mod.get('downloads')
        print(mod.get('title'))
        saved_projects.append(
            [mod.get('title'), mod.get('description'), 0,
             'https://modrinth.com/' + mod.get('project_type') + '/' + mod.get('slug'), mod.get('downloads'),
             'Modrinth'])
        download_count.append(mod.get('downloads'))

    return counted_downloads


def get_curseforge_downloads(user_id):
    counted_downloads = 0
    response = requests.get('https://api.curse.tools/v1/cf/mods/search', params={'gameId': '432', 'authorId': '{}'.format(user_id)}, timeout=30)

    print('CurseForge status:', response.status_code)
    print('CurseForge content type:', response.headers.get('Content-Type'))

    response.raise_for_status()

    try:
        response = response.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError('CurseForge returned invalid JSON: {}'.format(response.text[:500]))

    for project in response.get('data'):

        print(project.get('name'))
        counted_downloads += project.get('downloadCount')
        for gm_project in saved_projects:
            if gm_project[5] == 'Github':
                continue
            if gm_project[0].strip() == project.get('name').strip():
                og_downs = gm_project[4]
                gm_project[4] = gm_project[4] + project.get('downloadCount')
                for i in range(0, len(download_count)):
                    if download_count[i] == og_downs:
                        download_count[i] = og_downs + project.get('downloadCount')
                        break

    return counted_downloads


def get_github_projects_string(projects, user):
    project_string = ''
    for project in projects:
        if project[2] >= 1:
            project_string += '- [{}](https://github.com/{}/{}) - {}\n'.format(project[0].replace('-', ' '), user,
                                                                             project[0], project[1])
    return project_string


def get_most_downloaded_string():
    downloaded_string = ''
    download_count.sort(reverse=True)

    print(download_count)
    for project in saved_projects:
        print(project)

    for i in range(0, len(download_count)):
        for p in range(0, len(saved_projects)):
            if download_count[i] <= 0:
                continue
            if saved_projects[p][4] == download_count[i]:
                downloaded_string += '- {} - {} downloads  \n'.format(saved_projects[p][0].replace('-', ' '),
                                                                      f"{saved_projects[p][4]:,}")
                download_count[i] = -1
                saved_projects.pop(p)
                break

    return downloaded_string


total_downloads = 0

total_downloads += get_github_downloads('jacksonhickey')
total_downloads += get_modrinth_downloads('declipsonator')
total_downloads += get_curseforge_downloads(101367014)

template = requests.get('https://raw.githubusercontent.com/jacksonhickey/jacksonhickey/main/template.md').text
downloads_list = list(str(total_downloads))
if len(downloads_list) > 3:
    threes = int(len(downloads_list) / 3)
    start = len(downloads_list) - threes * 3
    full_string = ""
    for i in range(0, start):
        full_string += downloads_list[i]
    for i in range(start, len(downloads_list)):
        if (i - start) % 3 == 0:
            full_string += ","
        full_string += downloads_list[i]
template = template.replace('{downloads}', str(full_string)) \
    .replace('{projects}', get_github_projects_string(saved_projects, 'jacksonhickey')) \
    .replace('{last_updated}', datetime.utcnow().strftime('%Y-%m-%d %H:%M (UTC)')) \
    .replace('{rankings}', get_most_downloaded_string())

with open('README.md', 'w', encoding='UTF-8') as f:
    f.write(template)
    f.close()
