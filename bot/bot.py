#!/usr/bin/my_venv python
# -*- coding: utf-8 -*-

import csv
import datetime
import json
import os
import random
import selenium
import glob

from instapy import InstaPy, smart_run
from settings import COMMENTS, FRIENDS_DONT_INCLUDE, TAGS_DONT_LIKE, TAGS_TO_LIKE
from pathlib import Path

try:
    from settings import USERS_DATA
except ImportError:
    exit('Do cp settings.py.default settings.py and set login and password!')


def csv_to_list(file_csv):
    csv_list = []
    file_csv.seek(0)
    reader_csv = csv.reader(file_csv)
    for row in reader_csv:
        if row:
            csv_list.append(row[0])
    return csv_list


def flip_coin():
    return random.choices(['tags', 'followers', 'following'], [70, 15, 15], k=1)[0]


class Bot:

    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.comments = COMMENTS
        self.like = TAGS_TO_LIKE
        self.home_directory = str(Path.home())
        self.path = f'{self.home_directory}/InstaPy/logs/{login}/relationship_data/{login}'
        self.session = None

    def action(self, action, count=3, comments=True):
        """
        main bot process
        Three type of action for tags, followers and following
        :param action:
        can be tags, follower or following (string) flag to select action
        :param count:
        for followers and following - defines counts of photo which be liked
        :param comments:
        for followers and following - defines will be comments or not
        :return:
        start instapy smart_run
        """
        try:
            self.delete_cookie()
            self.session = self.open_session()
            # self.session.browser.delete_cookie(name=self.login) # TODO delete_cookie func built-in in instapy
            with smart_run(self.session):
                # bots settings
                # do not interact with users who have more than 8500 subscribers
                self.session.set_relationship_bounds(enabled=True, max_followers=8500)
                # setting rules for interaction with private users
                self.session.set_skip_users(skip_private=False,
                                            private_percentage=100,
                                            skip_no_profile_pic=True,
                                            no_profile_pic_percentage=100,
                                            skip_business=False,
                                            skip_non_business=False,
                                            business_percentage=100,
                                            skip_business_categories=[],
                                            dont_skip_business_categories=[],
                                            skip_bio_keyword=[],
                                            mandatory_bio_keywords=[])
                # setting interaction peaks per hour/day for likes/comments/subscriptions/server hits
                self.session.set_quota_supervisor(enabled=True,
                                                  sleep_after=["likes", "comments_d", "follows", "unfollows",
                                                               "server_calls_h"],
                                                  sleepyhead=True,
                                                  stochastic_flow=True,
                                                  notify_me=True,
                                                  peak_likes_hourly=57,
                                                  peak_likes_daily=585,
                                                  peak_comments_hourly=21,
                                                  peak_comments_daily=182,
                                                  peak_follows_hourly=48,
                                                  peak_follows_daily=None,
                                                  peak_unfollows_hourly=35,
                                                  peak_unfollows_daily=402,
                                                  peak_server_calls_hourly=None,
                                                  peak_server_calls_daily=4700)
                self.session.set_comments(self.comments)
                self.session.logger.info(f'Выбрали действие - {action}')
                self.session.set_dont_like(TAGS_DONT_LIKE)
                self.session.set_dont_include(FRIENDS_DONT_INCLUDE)

                # activity
                if action == 'tags':
                    self.session.set_do_follow(True, percentage=15)
                    self.session.set_do_comment(enabled=True, percentage=20)
                    self.session.like_by_tags(self.like, amount=250, randomize=True)
                elif action == 'followers' or 'following':
                    if comments:
                        self.session.set_do_comment(enabled=True, percentage=15)
                    self.session.set_do_like(True, percentage=90)
                    users_list = self.get_random_users(action=action, count=count)
                    # TODO rename count
                    self.session.like_by_users(users_list, amount=int(250 / count), randomize=False)
                else:
                    raise Exception('Available actions: tags, followers и following')
        except selenium.common.exceptions.WebDriverException as ex:
            print(ex)
            pass

    def delete_cookie(self):
        path_to_log_text = f'{self.home_directory}/InstaPy/logs/{self.login}/{self.login}_cookie.pkl'
        path_to_log = os.path.abspath(path_to_log_text)
        if os.path.exists(path_to_log):
            os.remove(path_to_log)

    def open_session(self):
        # get an InstaPy session!
        # set headless_browser=True to run InstaPy in the background
        return InstaPy(
            username=self.login,
            password=self.password,
            headless_browser=False,
            want_check_browser=False,
            bypass_security_challenge_using='sms'
        )

    def get_follower_or_following_list(self, action):
        if action == 'followers':
            self.session.grab_followers(username=self.login, amount="full", live_match=True, store_locally=True)
        elif action == 'following':
            self.session.grab_following(username=self.login, amount="full", live_match=True, store_locally=True)
        else:
            raise Exception('Available actions: followers и following')

    def get_latest_file(self, action):
        """
        search the newest json file list of followers/following in directory creating by InstaPy
        :param action:
        followers or following
        :return:
        return the newest (by date) json file with followers/following list
        """
        if os.path.exists(f'{self.path}/{action}/'):
            for dirpath, dirnames, files in os.walk(f'{self.path}/{action}/'):
                if not files:
                    self.get_follower_or_following_list(action=action)
        else:
            self.get_follower_or_following_list(action=action)
        list_of_files = glob.glob(f'{self.path}/{action}//*.json')
        return max(list_of_files, key=os.path.getctime)

    def get_random_users(self, count, action):
        """
        Take count random users from list of followers/following. They save to csv table, if user already in table
        take next one. When all users processed func create new list, old list save with date prefix
        :param count:
        count of random users (int)
        :param action:
        followers or following
        :return:
        list of random users 'count' long
        """
        latest_follower_json = self.get_latest_file(action)
        random_followers = []
        path_to_action_folder = f'csv_data/{self.login}/{action}'

        if not os.path.exists(path_to_action_folder):
            os.makedirs(path_to_action_folder)
        with open(f'{path_to_action_folder}/{action}_data.csv', 'a+', encoding='UTF8', newline='') as csv_data:
            with open(latest_follower_json, 'r') as json_data:
                while len(random_followers) < count:
                    csv_list = csv_to_list(csv_data)
                    json_data.seek(0)
                    follower_full_list = json.load(json_data)
                    if set(csv_list) != set(follower_full_list):
                        csv_data.seek(0)
                        reader = csv.reader(csv_data)
                        random_follower = random.choice(follower_full_list)
                        if [random_follower] in list(reader):
                            continue
                        writer = csv.writer(csv_data)
                        writer.writerow([random_follower])
                        random_followers.append(random_follower)
                    else:
                        csv_data.close()
                        self.get_follower_or_following_list(action)
                        if os.path.exists(
                                f'{path_to_action_folder}/{action}_{datetime.date.today().strftime("%b-%d-%Y")}.csv'):
                            pass
                        else:
                            os.rename(f'{path_to_action_folder}/{action}_data.csv',
                                      f'{path_to_action_folder}/{action}_{datetime.date.today().strftime("%b-%d-%Y")}.csv')
                        break
        return random_followers


if __name__ == '__main__':
    Bot(**USERS_DATA[1]).action(action=flip_coin(), count=50)
