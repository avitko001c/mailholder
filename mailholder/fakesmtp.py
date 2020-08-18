import argparse
import asyncore
import errno
import logging
import os
import shutil
import signal
import smtpd
import time


class FakeSMTPServer(smtpd.SMTPServer):
    """
    A SMTP server that catches all outgoing messages and saves them to
    a file. Messages are not sent to the recipients. Useful for
    testing mail functionality of other systems.
    """
    def __init__(self, localaddr, mail_dir):
        smtpd.SMTPServer.__init__(self, localaddr, None)
        self.mail_dir = mail_dir

        self.logger = logging.getLogger('fakesmtpd')
        self.logger.info("SMTP server started")
        self.logger.info("Mail directory %s", self.mail_dir)

    def process_message(self, peer, mailfrom, rcpttos, data):
        """
        Write outgoing mail data to a temporary file. Write one file
        per recipient.
        """
        self.logger.info("Incoming mail from %s", mailfrom)
        for recipient in rcpttos:
            self.logger.info("Logging mail for %s", recipient)
            filename = "{}.{:f}.mail".format(recipient, time.time())
            path = os.path.join(self.mail_dir, filename)
            with open(path, 'w') as f:
                f.write(data)
                f.write('\n')


def fakesmtpd_parser():
    """
    Return a command line parser for starting the SMTP server from the
    command line.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', default='localhost')
    parser.add_argument('-p', '--port', type=int, default=25)
    parser.add_argument(
        '--mail-dir',
        required=True,
        help="directory to save incoming mail")
    parser.add_argument(
        '--log-file',
        help="send output to a log file instead of stdout")
    return parser


def attach_signal_handlers(server):
    """Attach signal handlers to cleanly shutdown the SMTP server."""
    signals = {
        signal.SIGINT: 'SIGINT',
        signal.SIGTERM: 'SIGTERM',
    }

    def shutdown(signum, _frame):
        """
        Log the signal received and close the SMTP server's
        socket. The asyncore loop will end once all servers are
        closed.
        """
        server.logger.info("Received signal {}".format(signals[signum]))
        server.logger.info("Shutting down SMTP server")
        server.close()

    for signum in signals.keys():
        signal.signal(signum, shutdown)


def main():
    """Parse the command line arguments and start the SMTP server."""
    parser = fakesmtpd_parser()
    args = parser.parse_args()
    try:
        os.makedirs(args.mail_dir, 0o775)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    logging.basicConfig(filename=args.log_file, level=logging.DEBUG)

    server = FakeSMTPServer((args.host, args.port), args.mail_dir)
    attach_signal_handlers(server)
    asyncore.loop()
    shutil.rmtree(args.mail_dir)