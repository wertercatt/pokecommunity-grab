import time
import os
import os.path
import shutil
import glob

from seesaw.project import *
from seesaw.config import *
from seesaw.item import *
from seesaw.task import *
from seesaw.pipeline import *
from seesaw.externalprocess import *
from seesaw.tracker import *

DATA_DIR = "data"
USER_AGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27"
VERSION = "20170517.03"

class PrepareDirectories(SimpleTask):
  def __init__(self):
    SimpleTask.__init__(self, "PrepareDirectories")

  def process(self, item):
    item_name = item["item_name"]
    dirname = "/".join(( DATA_DIR, item_name ))

    if os.path.isdir(dirname):
      shutil.rmtree(dirname)

    os.makedirs(dirname + "/files")

    item["item_dir"] = dirname
    item["data_dir"] = DATA_DIR
    item["warc_file_base"] = "forums.steampowered.com-threads-range-%s-%s" % (item_name, time.strftime("%Y%m%d-%H%M%S"))

class MoveFiles(SimpleTask):
  def __init__(self):
    SimpleTask.__init__(self, "MoveFiles")

  def process(self, item):
    os.rename("%(item_dir)s/%(warc_file_base)s.warc.gz" % item,
              "%(data_dir)s/%(warc_file_base)s.warc.gz" % item)

    shutil.rmtree("%(item_dir)s" % item)

class DeleteFiles(SimpleTask):
  def __init__(self):
    SimpleTask.__init__(self, "DeleteFiles")

  def process(self, item):
    os.unlink("%(data_dir)s/%(warc_file_base)s.warc.gz" % item)

def calculate_item_id(item):
  thread_htmls = glob.glob("%(item_dir)s/files/forums.steampowered.com/showthread.php*" % item)
  n = len(thread_htmls)
  if n == 0:
    return "null"
  else:
    return thread_htmls[0] + "-" + thread_htmls[n-1]


project = Project(
  title = "Steam Users' Forum",
  project_html = """
    <img class="project-logo" alt="Steam Logo" src="http://archiveteam.org/images/4/48/Steam_Icon_2014.png" />
    <h2>Steam Users' Forum <span class="links"><a href="http://forums.steampowered.com/forums">Website</a> &middot; <a href="http://tracker.archiveteam.org/spuf-grab/">Leaderboard</a></span></h2>
    <p>Getting killed June 5th.</p>
  """,
  utc_deadline = datetime.datetime(2017,06,04, 23,59,0)
)

pipeline = Pipeline(
  GetItemFromTracker("http://tracker.archiveteam.org/spuf-grab", downloader, VERSION),
  PrepareDirectories(),
  WgetDownload([ "./wget-lua",
      "-U", USER_AGENT,
      "-nv",
      "-o", ItemInterpolation("%(item_dir)s/wget.log"),
      "--directory-prefix", ItemInterpolation("%(item_dir)s/files"),
      "--keep-session-cookies",
      "--save-cookies", ItemInterpolation("%(item_dir)s/files/cookies.txt"),
      "--force-directories",
      "--adjust-extension",
      "-e", "robots=off",
      "--page-requisites", "--span-hosts",
      "--lua-script", "vbulletin.lua",
      "--timeout", "10",
      "--tries", "3",
      "--waitretry", "5",
	  "--header", "Cookie: bblastvisit=1495056394; __utmt=1; bblastactivity=0; bbsessionhash=03948598c9a709717277ba412e5ff352; bbforum_view=e62f44913aeb32d4ddc2ee89de61e6c886b6992da-2-%7Bi-14_i-1495057128_i-1189_i-1495057156_%7D; __utma=127613338.730818989.1493599611.1495044823.1495054243.8; __utmb=127613338.150.10.1495054243; __utmc=-127613338; __utmz=127613338.1494988830.5.3.utmcsr=chat.efnet.org:9090|utmccn=(referral)|utmcmd=referral|utmcct=/"
      "--warc-file", ItemInterpolation("%(item_dir)s/%(warc_file_base)s"),
      "--warc-header", "operator: Archive Team",
      "--warc-header", "spuf-grab-script-version: " + VERSION,
      "--warc-header", ItemInterpolation("spuf-threads-range: %(item_name)s"),
      ItemInterpolation("http://forums.steampowered.com/forums/external.php?type=RSS2"), # initializes the cookies
      ItemInterpolation("http://forums.steampowered.com/forums/showthread.php?t=%(item_name)s0&amp;daysprune=-1"),
      ItemInterpolation("http://forums.steampowered.com/forums/showthread.php?t=%(item_name)s1&amp;daysprune=-1"),
      ItemInterpolation("http://forums.steampowered.com/forums/showthread.php?t=%(item_name)s2&amp;daysprune=-1"),
      ItemInterpolation("http://forums.steampowered.com/forums/showthread.php?t=%(item_name)s3&amp;daysprune=-1"),
      ItemInterpolation("http://forums.steampowered.com/forums/showthread.php?t=%(item_name)s4&amp;daysprune=-1"),
      ItemInterpolation("http://forums.steampowered.com/forums/showthread.php?t=%(item_name)s5&amp;daysprune=-1"),
      ItemInterpolation("http://forums.steampowered.com/forums/showthread.php?t=%(item_name)s6&amp;daysprune=-1"),
      ItemInterpolation("http://forums.steampowered.com/forums/showthread.php?t=%(item_name)s7&amp;daysprune=-1"),
      ItemInterpolation("http://forums.steampowered.com/forums/showthread.php?t=%(item_name)s8&amp;daysprune=-1"),
      ItemInterpolation("http://forums.steampowered.com/forums/showthread.php?t=%(item_name)s9&amp;daysprune=-1")
    ],
    max_tries = 2,
    accept_on_exit_code = [ 0, 4, 6, 8 ],
  ),
  PrepareStatsForTracker(
    defaults = { "downloader": downloader, "version": VERSION },
    file_groups = {
      "data": [ ItemInterpolation("%(item_dir)s/%(warc_file_base)s.warc.gz") ]
    },
    id_function = calculate_item_id
  ),
  MoveFiles(),
  LimitConcurrent(1,
    RsyncUpload(
      target = ConfigInterpolation("fos.textfiles.com::alardland/warrior/spuf-grab/%s/", downloader),
      target_source_path = ItemInterpolation("%(data_dir)s/"),
      files = [
        ItemInterpolation("%(warc_file_base)s.warc.gz")
      ],
      extra_args = [
        "--partial",
        "--partial-dir", ".rsync-tmp"
      ]
    ),
  ),
  SendDoneToTracker(
    tracker_url = "http://tracker.archiveteam.org/spuf-grab",
    stats = ItemValue("stats")
  ),
  DeleteFiles()
)

