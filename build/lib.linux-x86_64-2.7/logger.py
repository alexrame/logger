# -*- coding: utf-8 -*-

import __main__
import logging
import os
import sys

from logging.config import fileConfig
from logutils.colorize import ColorizingStreamHandler

# CODE FROM https://opensourcehacker.com/2013/03/14/ultima-python-logger-somewhere-over-the-rainbow/
class RainbowLoggingHandler(ColorizingStreamHandler):
    """ A colorful logging handler optimized for terminal debugging aestetichs.

    - Designed for diagnosis and debug mode output - not for disk logs

    - Highlight the content of logging message in more readable manner

    - Show function and line, so you can trace where your logging messages
      are coming from

    - Keep timestamp compact

    - Extra module/function output for traceability

    The class provide few options as member variables you
    would might want to customize after instiating the handler.
    """

    # Define color for message payload
    level_map = {
        logging.DEBUG: (None, 'cyan', False),
        logging.INFO: (None, 'white', False),
        logging.WARNING: (None, 'yellow', True),
        logging.ERROR: (None, 'red', True),
        logging.CRITICAL: ('red', 'white', True),
    }

    date_format = "%H:%m:%S"

    #: How many characters reserve to function name logging
    who_padding = 22
    name_padding = 40

    #: Show logger name
    show_name = True

    def get_color(self, fg=None, bg=None, bold=False):
        """
        Construct a terminal color code

        :param fg: Symbolic name of foreground color

        :param bg: Symbolic name of background color

        :param bold: Brightness bit
        """
        params = []
        if bg in self.color_map:
            params.append(str(self.color_map[bg] + 40))
        if fg in self.color_map:
            params.append(str(self.color_map[fg] + 30))
        if bold:
            params.append('1')

        color_code = ''.join((self.csi, ';'.join(params), 'm'))

        return color_code

    def colorize(self, record):
        """
        Get a special format string with ASCII color codes.
        """

        # Dynamic message color based on logging level
        if record.levelno in self.level_map:
            fg, bg, bold = self.level_map[record.levelno]
        else:
            # Defaults
            bg = None
            fg = "white"
            bold = False

        # Magician's hat
        # https://www.youtube.com/watch?v=1HRa4X07jdE
        template = [
            "[",
            self.get_color("black", None, True),
            "%(asctime)s",
            self.reset,
            "] ",
            self.get_color("white", None, True) if self.show_name else "",
            "%(padded_name)s" if self.show_name else "",
            #"%(padded_who)s",
            self.reset,
            #" ",
            self.get_color(bg, fg, bold),
            "%(message)s",
            self.reset,
        ]

        format = "".join(template)

        who = [self.get_color("green"),
               getattr(record, "funcName", ""),
               "()",
               self.get_color("black", None, True),
               ":",
               self.get_color("cyan"),
               str(getattr(record, "lineno", 0))]

        who = "".join(who)

        # We need to calculate padding length manualy
        # as color codes mess up string length based calcs
        unformatted_who = getattr(record, "funcName", "") + "()" + \
            ":" + str(getattr(record, "lineno", 0))

        if len(unformatted_who) < self.who_padding:
            spaces = " " * (self.who_padding - len(unformatted_who))
        else:
            spaces = ""

        record.padded_who = who + spaces


        unformatted_name = getattr(record, "name", "")
        if len(unformatted_name) < self.name_padding:
            spaces = " " * (self.name_padding - len(unformatted_name))
        else:
            unformatted_name = "..." + unformatted_name[-self.name_padding + 1:][3:]
            spaces = " "
        record.padded_name = unformatted_name + spaces

        formatter = logging.Formatter(format, self.date_format)
        self.colorize_traceback(formatter, record)
        output = formatter.format(record)
        # Clean cache so the color codes of traceback don't leak to other formatters
        record.ext_text = None
        return output

    def colorize_traceback(self, formatter, record):
        """
        Turn traceback text to red.
        """
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            record.exc_text = "".join([
                self.get_color("red"),
                formatter.formatException(record.exc_info),
                self.reset,
            ])

    def format(self, record):
        """
        Formats a record for output.
        Takes a custom formatting path on a terminal.
        """
        if self.is_tty:
            message = self.colorize(record)
        else:
            message = logging.StreamHandler.format(self, record)

        return message


def get_config_logger(name):
    LOG_SETTINGS = {
    'version': 1,
    'keys': ["root"],
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': '/tmp/junk.log',
            'mode': 'a',
            'maxBytes': 10485760,
            'backupCount': 5,
        },

    },
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
        'email': {
            'format': 'Timestamp: %(asctime)s\nModule: %(module)s\n' \
            'Line: %(lineno)d\nMessage: %(message)s',
        },
    },
    'loggers': {
        '': {
            'level':'DEBUG',
            'handlers': ['console']
            },
    }}
    logger = logging.getLogger(name)        
    logging.config.dictConfig(LOG_SETTINGS)

    return logger

def get_default_logger(name):
    logger = logging.getLogger(name)
    logger.propagate = False
    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        # add the handlers to logger
        logger.addHandler(ch) 
    return logger

def get_color_logger(name):
    logger = logging.getLogger(name)
    logger.propagate = False
    
    if not logger.handlers:
        handler = RainbowLoggingHandler(sys.stdout)
        logger.addHandler(handler)
    
    return logger   

def choose_logger(name, use_color):
    if use_color:
        return get_color_logger(name)
    elif False:
        return get_default_logger(name)
    else:
         return get_config_logger(name)
            
def set_level(logger, level):
    if "LOGLEVEL" in os.environ:
        logger.setLevel(os.environ["LOGLEVEL"])
    else:
        logger.setLevel(level)

def get_name_main():
    name_main = __main__.__file__
    if name_main.endswith(".py"):
        name_main = name_main[:-3]
    if "/" in name_main:
        name_main = ".".join(name_main.split("/")[-2:])
    return  name_main
    
def modify_name(name, shorten):
    if hasattr(__main__, "__file__"):
        name_main = get_name_main()
        name = name_main + ": " + name
    if shorten and len(name) > 40:
        name = "..." + name[-40 + 1:][3:]
    return name
    
def get_logger(name, use_color=False, level=logging.INFO, shorten=False):

    name = modify_name(name, shorten=shorten)
    logger = choose_logger(name, use_color=use_color)
    set_level(logger, level)
    
    return logger

