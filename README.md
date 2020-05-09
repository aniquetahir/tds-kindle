# Introduction
This is a script to get articles from 'Towards Data Science' blog and create a kindle document out of it.


# Features
- Easy to set up a cron job to send you daily updates
- Sections to move between articles
- No article limit!
- No paywalls!

# Limitations
- Kindle only allows maximum of 10MB files to be sent over email

# Installation
Please make sure python3, node, yarn are installed.
Firefox path and Geckodriver path can be updated in `local.env.sh` file.
The following command will install dependencies:  
```shell script
./setup.sh
```


# Usage

```shell script
./local.env.sh && ./main.py
```
