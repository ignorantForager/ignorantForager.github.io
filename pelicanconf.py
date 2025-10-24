AUTHOR = 'Cadence James'
SITENAME = 'HomeLab Documents'
SITEURL = ""
PATH = "content"
TIMEZONE = 'America/Los_Angeles'
DEFAULT_LANG = 'en'
THEME = 'themes/my-theme'
MENUITEMS = (
  ('Home', '/'),
  ('Tags', '/tags'),
  ('Categories', '/categories'),
)
DISPLAY_CATEGORIES_ON_MENU = False
SUMMARY_MAX_LENGTH = 100
# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
LINKS = ()
SOCIAL = ()
DEFAULT_PAGINATION = 10
STATIC_PATHS = ['images', 'extra/favicon.ico'
EXTRA_PATH_METADATA = {
    'extra/favicon.ico': {'path': 'favicon.ico'},
}
# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True
