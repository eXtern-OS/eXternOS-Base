# Copyright 2008 Canonical Ltd.

# This file is part of launchpadlib.
#
# launchpadlib is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, version 3 of the License.
#
# launchpadlib is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with launchpadlib. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

"""launchpadlib credentials and authentication support."""

__metaclass__ = type
__all__ = [
    'AccessToken',
    'AnonymousAccessToken',
    'AuthorizeRequestTokenWithBrowser',
    'CredentialStore',
    'RequestTokenAuthorizationEngine',
    'Consumer',
    'Credentials',
    ]

import cgi
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

import httplib2
import os
from select import select
import stat
from sys import stdin
import time
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin
import webbrowser
from base64 import (
    b64decode,
    b64encode,
    )

try:
    import json
except ImportError:
    import simplejson as json

if bytes is str:
    # Python 2
    unicode_type = unicode
else:
    unicode_type = str
    
from lazr.restfulclient.errors import HTTPError
from lazr.restfulclient.authorize.oauth import (
    AccessToken as _AccessToken,
    Consumer,
    OAuthAuthorizer,
    SystemWideConsumer # Not used directly, just re-imported into here.
    )

from launchpadlib import uris

request_token_page = '+request-token'
access_token_page = '+access-token'
authorize_token_page = '+authorize-token'
access_token_poll_time = 1
access_token_poll_timeout = 15 * 60

EXPLOSIVE_ERRORS = (MemoryError, KeyboardInterrupt, SystemExit)


def _ssl_certificate_validation_disabled():
    """Whether the user has disabled SSL certificate connection.

    Some testing servers have broken certificates.  Rather than raising an
    error, we allow an environment variable,
    ``LP_DISABLE_SSL_CERTIFICATE_VALIDATION`` to disable the check.
    """
    # XXX: Copied from lazr/restfulclient/_browser.py.  Once it appears in a
    # released version of lazr.restfulclient, depend on that new version and
    # delete this copy.
    return bool(
        os.environ.get('LP_DISABLE_SSL_CERTIFICATE_VALIDATION', False))


def _http_post(url, headers, params):
    """POST to ``url`` with ``headers`` and a body of urlencoded ``params``.

    Wraps it up to make sure we avoid the SSL certificate validation if our
    environment tells us to.  Also, raises an error on non-200 statuses.
    """
    cert_disabled = _ssl_certificate_validation_disabled()
    response, content = httplib2.Http(
        disable_ssl_certificate_validation=cert_disabled).request(
        url, method='POST', headers=headers, body=urlencode(params))
    if response.status != 200:
        raise HTTPError(response, content)
    return response, content


class Credentials(OAuthAuthorizer):
    """Standard credentials storage and usage class.

    :ivar consumer: The consumer (application)
    :type consumer: `Consumer`
    :ivar access_token: Access information on behalf of the user
    :type access_token: `AccessToken`
    """
    _request_token = None

    URI_TOKEN_FORMAT = "uri"
    DICT_TOKEN_FORMAT = "dict"
    ITEM_SEPARATOR = '<BR>'
    NEWLINE = '\n'

    def serialize(self):
        """Turn this object into a string.

        This should probably be moved into OAuthAuthorizer.
        """
        sio = StringIO()
        self.save(sio)
        serialized = sio.getvalue()
        if isinstance(serialized, unicode_type):
            serialized = serialized.encode('utf-8')
        return serialized

    @classmethod
    def from_string(cls, value):
        """Create a `Credentials` object from a serialized string.

        This should probably be moved into OAuthAuthorizer.
        """
        credentials = cls()
        if not isinstance(value, unicode_type):
            value = value.decode('utf-8')
        credentials.load(StringIO(value))
        return credentials

    def get_request_token(self, context=None, web_root=uris.STAGING_WEB_ROOT,
                          token_format=URI_TOKEN_FORMAT):
        """Request an OAuth token to Launchpad.

        Also store the token in self._request_token.

        This method must not be called on an object with no consumer
        specified or if an access token has already been obtained.

        :param context: The context of this token, that is, its scope of
            validity within Launchpad.
        :param web_root: The URL of the website on which the token
            should be requested.
        :token_format: How the token should be
            presented. URI_TOKEN_FORMAT means just return the URL to
            the page that authorizes the token.  DICT_TOKEN_FORMAT
            means return a dictionary describing the token
            and the site's authentication policy.

        :return: If token_format is URI_TOKEN_FORMAT, the URL for the
            user to authorize the `AccessToken` provided by
            Launchpad. If token_format is DICT_TOKEN_FORMAT, a dict of
            information about the new access token.
        """
        assert self.consumer is not None, "Consumer not specified."
        assert self.access_token is None, "Access token already obtained."
        web_root = uris.lookup_web_root(web_root)
        params = dict(
            oauth_consumer_key=self.consumer.key,
            oauth_signature_method='PLAINTEXT',
            oauth_signature='&')
        url = web_root + request_token_page
        headers = {'Referer': web_root}
        if token_format == self.DICT_TOKEN_FORMAT:
            headers['Accept'] = 'application/json'
        response, content = _http_post(url, headers, params)
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        if token_format == self.DICT_TOKEN_FORMAT:
            params = json.loads(content)
            if context is not None:
                params["lp.context"] = context
            self._request_token = AccessToken.from_params(params)
            return params
        else:
            self._request_token = AccessToken.from_string(content)
            url = '%s%s?oauth_token=%s' % (web_root, authorize_token_page,
                                           self._request_token.key)
            if context is not None:
                self._request_token.context = context
                url += "&lp.context=%s" % context
            return url

    def exchange_request_token_for_access_token(
        self, web_root=uris.STAGING_WEB_ROOT):
        """Exchange the previously obtained request token for an access token.

        This method must not be called unless get_request_token() has been
        called and completed successfully.

        The access token will be stored as self.access_token.

        :param web_root: The base URL of the website that granted the
            request token.
        """
        assert self._request_token is not None, (
            "get_request_token() doesn't seem to have been called.")
        web_root = uris.lookup_web_root(web_root)
        params = dict(
            oauth_consumer_key=self.consumer.key,
            oauth_signature_method='PLAINTEXT',
            oauth_token=self._request_token.key,
            oauth_signature='&%s' % self._request_token.secret)
        url = web_root + access_token_page
        headers = {'Referer': web_root}
        response, content = _http_post(url, headers, params)
        self.access_token = AccessToken.from_string(content)


class AccessToken(_AccessToken):
    """An OAuth access token."""

    @classmethod
    def from_params(cls, params):
        """Create and return a new `AccessToken` from the given dict."""
        key = params['oauth_token']
        secret = params['oauth_token_secret']
        context = params.get('lp.context')
        return cls(key, secret, context)

    @classmethod
    def from_string(cls, query_string):
        """Create and return a new `AccessToken` from the given string."""
        if not isinstance(query_string, unicode_type):
            query_string = query_string.decode('utf-8')
        params = cgi.parse_qs(query_string, keep_blank_values=False)
        key = params['oauth_token']
        assert len(key) == 1, (
            "Query string must have exactly one oauth_token.")
        key = key[0]
        secret = params['oauth_token_secret']
        assert len(secret) == 1, "Query string must have exactly one secret."
        secret = secret[0]
        context = params.get('lp.context')
        if context is not None:
            assert len(context) == 1, (
                "Query string must have exactly one context")
            context = context[0]
        return cls(key, secret, context)


class AnonymousAccessToken(_AccessToken):
    """An OAuth access token that doesn't authenticate anybody.

    This token can be used for anonymous access.
    """
    def __init__(self):
        super(AnonymousAccessToken, self).__init__('','')


class CredentialStore(object):
    """Store OAuth credentials locally.

    This is a generic superclass. To implement a specific way of
    storing credentials locally you'll need to subclass this class,
    and implement `do_save` and `do_load`.
    """

    def __init__(self, credential_save_failed=None):
        """Constructor.

        :param credential_save_failed: A callback to be invoked if the
            save to local storage fails. You should never invoke this
            callback yourself! Instead, you should raise an exception
            from do_save().
        """
        self.credential_save_failed = credential_save_failed

    def save(self, credentials, unique_consumer_id):
        """Save the credentials and invoke the callback on failure.

        Do not override this method when subclassing. Override
        do_save() instead.
        """
        try:
            self.do_save(credentials, unique_consumer_id)
        except EXPLOSIVE_ERRORS:
            raise
        except Exception as e:
            if self.credential_save_failed is None:
                raise e
            self.credential_save_failed()
        return credentials

    def do_save(self, credentials, unique_consumer_id):
        """Store newly-authorized credentials locally for later use.

        :param credentials: A Credentials object to save.
        :param unique_consumer_id: A string uniquely identifying an
            OAuth consumer on a Launchpad instance.
        """
        raise NotImplementedError()

    def load(self, unique_key):
        """Retrieve credentials from a local store.

        This method is the inverse of `save`.

        There's no special behavior in this method--it just calls
        `do_load`. There _is_ special behavior in `save`, and this
        way, developers can remember to implement `do_save` and
        `do_load`, not `do_save` and `load`.

        :param unique_key: A string uniquely identifying an OAuth consumer
            on a Launchpad instance.

        :return: A `Credentials` object if one is found in the local
            store, and None otherise.
        """
        return self.do_load(unique_key)

    def do_load(self, unique_key):
        """Retrieve credentials from a local store.

        This method is the inverse of `do_save`.

        :param unique_key: A string uniquely identifying an OAuth consumer
            on a Launchpad instance.

        :return: A `Credentials` object if one is found in the local
            store, and None otherise.
        """
        raise NotImplementedError()


class KeyringCredentialStore(CredentialStore):
    """Store credentials in the GNOME keyring or KDE wallet.

    This is a good solution for desktop applications and interactive
    scripts. It doesn't work for non-interactive scripts, or for
    integrating third-party websites into Launchpad.
    """

    B64MARKER = b"<B64>"

    @staticmethod
    def _ensure_keyring_imported():
        """Ensure the keyring module is imported (postponing side effects).

        The keyring module initializes the environment-dependent backend at
        import time (nasty).  We want to avoid that initialization because it
        may do things like prompt the user to unlock their password store
        (e.g., KWallet).
        """
        if 'keyring' not in globals():
            global keyring
            import keyring

    def do_save(self, credentials, unique_key):
        """Store newly-authorized credentials in the keyring."""
        self._ensure_keyring_imported()
        serialized = credentials.serialize()
        # Some users have reported problems with corrupted keyrings, both in
        # Gnome and KDE, when newlines are included in the password.  Avoid
        # this problem by base 64 encoding the serialized value.
        serialized = self.B64MARKER + b64encode(serialized)
        keyring.set_password(
            'launchpadlib', unique_key, serialized.decode('utf-8'))

    def do_load(self, unique_key):
        """Retrieve credentials from the keyring."""
        self._ensure_keyring_imported()
        credential_string = keyring.get_password(
            'launchpadlib', unique_key)
        if credential_string is not None:
            if isinstance(credential_string, unicode_type):
                credential_string = credential_string.encode('utf8')
            if credential_string.startswith(self.B64MARKER):
                try:
                    credential_string = b64decode(
                        credential_string[len(self.B64MARKER):])
                except TypeError:
                    # The credential_string should be base 64 but cannot be
                    # decoded.
                    return None
            try:
                credentials = Credentials.from_string(credential_string)
                return credentials
            except:
                # If any error occurs at this point the most reasonable thing
                # to do is return no credentials, which will require
                # re-authorization but the user will be able to proceed.
                return None
        return None


class UnencryptedFileCredentialStore(CredentialStore):
    """Store credentials unencrypted in a file on disk.

    This is a good solution for scripts that need to run without any
    user interaction.
    """

    def __init__(self, filename, credential_save_failed=None):
        super(UnencryptedFileCredentialStore, self).__init__(
            credential_save_failed)
        self.filename = filename

    def do_save(self, credentials, unique_key):
        """Save the credentials to disk."""
        credentials.save_to_path(self.filename)

    def do_load(self, unique_key):
        """Load the credentials from disk."""
        if (os.path.exists(self.filename)
            and not os.stat(self.filename)[stat.ST_SIZE] == 0):
            return Credentials.load_from_path(self.filename)
        return None


class RequestTokenAuthorizationEngine(object):
    """The superclass of all request token authorizers.

    This base class does not implement request token authorization,
    since that varies depending on how you want the end-user to
    authorize a request token. You'll need to subclass this class and
    implement `make_end_user_authorize_token`.
    """

    UNAUTHORIZED_ACCESS_LEVEL = "UNAUTHORIZED"

    def __init__(self, service_root, application_name=None,
                 consumer_name=None, allow_access_levels=None):
        """Base class initialization.

        :param service_root: The root of the Launchpad instance being
            used.

        :param application_name: The name of the application that
            wants to use launchpadlib. This is used in conjunction
            with a desktop-wide integration.

            If you specify this argument, your values for
            consumer_name and allow_access_levels are ignored.

        :param consumer_name: The OAuth consumer name, for an
            application that wants its own point of integration into
            Launchpad. In almost all cases, you want to specify
            application_name instead and do a desktop-wide
            integration. The exception is when you're integrating a
            third-party website into Launchpad.

        :param allow_access_levels: A list of the Launchpad access
            levels to present to the user. ('READ_PUBLIC' and so on.)
            Your value for this argument will be ignored during a
            desktop-wide integration.
        :type allow_access_levels: A list of strings.
        """
        self.service_root = uris.lookup_service_root(service_root)
        self.web_root = uris.web_root_for_service_root(service_root)

        if application_name is None and consumer_name is None:
            raise ValueError(
                "You must provide either application_name or consumer_name.")

        if application_name is not None and consumer_name is not None:
            raise ValueError(
                "You must provide only one of application_name and "
                "consumer_name. (You provided %r and %r.)" % (
                    application_name, consumer_name))

        if consumer_name is None:
            # System-wide integration. Create a system-wide consumer
            # and identify the application using a separate
            # application name.
            allow_access_levels = ["DESKTOP_INTEGRATION"]
            consumer = SystemWideConsumer(application_name)
        else:
            # Application-specific integration. Use the provided
            # consumer name to create a consumer automatically.
            consumer = Consumer(consumer_name)
            application_name = consumer_name

        self.consumer = consumer
        self.application_name = application_name

        self.allow_access_levels = allow_access_levels or []

    @property
    def unique_consumer_id(self):
        """Return a string identifying this consumer on this host."""
        return self.consumer.key + '@' + self.service_root

    def authorization_url(self, request_token):
        """Return the authorization URL for a request token.

        This is the URL the end-user must visit to authorize the
        token. How exactly does this happen? That depends on the
        subclass implementation.
        """
        page = "%s?oauth_token=%s" % (authorize_token_page, request_token)
        allow_permission = "&allow_permission="
        if len(self.allow_access_levels) > 0:
            page += (
                allow_permission
                + allow_permission.join(self.allow_access_levels))
        return urljoin(self.web_root, page)

    def __call__(self, credentials, credential_store):
        """Authorize a token and associate it with the given credentials.

        If the credential store runs into a problem storing the
        credential locally, the `credential_save_failed` callback will
        be invoked. The callback will not be invoked if there's a
        problem authorizing the credentials.

        :param credentials: A `Credentials` object. If the end-user
            authorizes these credentials, this object will have its
            .access_token property set.

        :param credential_store: A `CredentialStore` object. If the
            end-user authorizes the credentials, they will be
            persisted locally using this object.

        :return: If the credentials are successfully authorized, the
            return value is the `Credentials` object originally passed
            in. Otherwise the return value is None.
        """
        request_token_string = self.get_request_token(credentials)
        # Hand off control to the end-user.
        self.make_end_user_authorize_token(credentials, request_token_string)
        if credentials.access_token is None:
            # The end-user refused to authorize the application.
            return None
        # save() invokes the callback on failure.
        credential_store.save(credentials, self.unique_consumer_id)
        return credentials

    def get_request_token(self, credentials):
        """Get a new request token from the server.

        :param return: The request token.
        """
        authorization_json = credentials.get_request_token(
            web_root=self.web_root,
            token_format=Credentials.DICT_TOKEN_FORMAT)
        return authorization_json['oauth_token']

    def make_end_user_authorize_token(self, credentials, request_token):
        """Authorize the given request token using the given credentials.

        Your subclass must implement this method: it has no default
        implementation.

        Because an access token may expire or be revoked in the middle
        of a session, this method may be called at arbitrary points in
        a launchpadlib session, or even multiple times during a single
        session (with a different request token each time).

        In most cases, however, this method will be called at the
        beginning of a launchpadlib session, or not at all.
        """
        raise NotImplementedError()


class AuthorizeRequestTokenWithBrowser(RequestTokenAuthorizationEngine):
    """The simplest (and, right now, the only) request token authorizer.

    This authorizer simply opens up the end-user's web browser to a
    Launchpad URL and lets the end-user authorize the request token
    themselves.
    """

    WAITING_FOR_USER = (
        "The authorization page:\n"
        " (%s)\n"
        "should be opening in your browser. Use your browser to authorize\n"
        "this program to access Launchpad on your behalf.")
    TIMEOUT_MESSAGE = "Press Enter to continue or wait (%d) seconds..."
    TIMEOUT = 5
    WAITING_FOR_LAUNCHPAD = (
            "Waiting to hear from Launchpad about your decision...")
    TERMINAL_BROWSERS = ('www-browser', 'links', 'links2', 'lynx',
                         'elinks', 'elinks-lite', 'netrik', 'w3m')

    def __init__(self, service_root, application_name, consumer_name=None,
                 credential_save_failed=None, allow_access_levels=None):
        """Constructor.

        :param service_root: See `RequestTokenAuthorizationEngine`.
        :param application_name: See `RequestTokenAuthorizationEngine`.
        :param consumer_name: The value of this argument is
            ignored. If we have the capability to open the end-user's
            web browser, we must be running on the end-user's computer,
            so we should do a full desktop integration.
        :param credential_save_failed: See `RequestTokenAuthorizationEngine`.
        :param allow_access_levels: The value of this argument is
            ignored, for the same reason as consumer_name.
        """
        # It doesn't look like we're doing anything here, but we
        # are discarding the passed-in values for consumer_name and
        # allow_access_levels.
        super(AuthorizeRequestTokenWithBrowser, self).__init__(
              service_root, application_name, None,
              credential_save_failed)

    def output(self, message):
        """Display a message.

        By default, prints the message to standard output. The message
        does not require any user interaction--it's solely
        informative.
        """
        print(message)

    def make_end_user_authorize_token(self, credentials, request_token):
        """Have the end-user authorize the token in their browser."""

        authorization_url = self.authorization_url(request_token)
        self.output(self.WAITING_FOR_USER % authorization_url)

        try:
            browser_obj = webbrowser.get()
            browser = getattr(browser_obj, "basename", None)
            console_browser = browser in self.TERMINAL_BROWSERS
        except webbrowser.Error:
            browser_obj = None
            console_browser = False

        if console_browser:
            self.output(self.TIMEOUT_MESSAGE % self.TIMEOUT)
            # Wait a little time before attempting to launch browser,
            # give users the chance to press a key to skip it anyway.
            rlist, _, _ = select([stdin], [], [], self.TIMEOUT)
            if rlist:
                stdin.readline()

        self.output(self.WAITING_FOR_LAUNCHPAD)
        if browser_obj is not None:
            webbrowser.open(authorization_url)
        start_time = time.time()
        while credentials.access_token is None:
            time.sleep(access_token_poll_time)
            try:
                credentials.exchange_request_token_for_access_token(
                    self.web_root)
                break
            except HTTPError as e:
                if e.response.status == 403:
                    # The user decided not to authorize this
                    # application.
                    raise EndUserDeclinedAuthorization(e.content)
                elif e.response.status == 401:
                    # The user has not made a decision yet.
                    pass
                else:
                    # There was an error accessing the server.
                    print("Unexpected response from Launchpad:")
                    print(e)
            if time.time() >= start_time + access_token_poll_timeout:
                raise TokenAuthorizationTimedOut(
                    "Timed out after %d seconds." % access_token_poll_timeout)


class TokenAuthorizationException(Exception):
    pass


class RequestTokenAlreadyAuthorized(TokenAuthorizationException):
    pass


class EndUserDeclinedAuthorization(TokenAuthorizationException):
    pass


class TokenAuthorizationTimedOut(TokenAuthorizationException):
    pass


class ClientError(TokenAuthorizationException):
    pass


class ServerError(TokenAuthorizationException):
    pass


class NoLaunchpadAccount(TokenAuthorizationException):
    pass


class TooManyAuthenticationFailures(TokenAuthorizationException):
    pass
