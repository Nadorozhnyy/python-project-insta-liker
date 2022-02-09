# <p align=center>InstaLiker</p>

---
## Table of contents

* [Description](#description)
* [Technologies](#technologies)
* [Project setup](#project-setup)
* [Future scope](#future-scope)
---
## Description

InstaLiker bot is based on lib Instapy.
Performs three functions with different percentage probability (in standard):
* like by tags (70%)
* like followers (15%)
* like following (15%)

All data is stored in settings.py. Data must be filled before work.

Login, password, tags to like, tags not to like, friends
what we shouldn't like and comments what will be posted 
in random order. 

The bot function is called with the count parameter, the number 
of users that will be taken to work from followers and following. 
Before starting work, the bot receives a list of followers and 
following and interacts with unique users on each iteration. 
When the entire list is passed, the bot loads a new list, 
the old one is saved. 

---
## Technologies
Project is created with:
* instapy version: 0.6.16

---
## Project setup
npm install pythonprojectinstaliker

---
## Future scope
* like users from followers and following your followers and following
