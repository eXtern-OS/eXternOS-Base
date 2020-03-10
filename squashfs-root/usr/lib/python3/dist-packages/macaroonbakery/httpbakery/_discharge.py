# Copyright 2017 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE file for details.
import macaroonbakery.bakery as bakery
import macaroonbakery._utils as utils


def discharge(ctx, content, key, locator, checker):
    '''Handles a discharge request as received by the /discharge
    endpoint.
    @param ctx The context passed to the checker {checkers.AuthContext}
    @param content URL and form parameters {dict}
    @param locator Locator used to add third party caveats returned by
    the checker {macaroonbakery.ThirdPartyLocator}
    @param checker {macaroonbakery.ThirdPartyCaveatChecker} Used to check third
    party caveats.
    @return The discharge macaroon {macaroonbakery.Macaroon}
    '''
    id = content.get('id')
    if id is None:
        id = content.get('id64')
        if id is not None:
            id = utils.b64decode(id)
    caveat = content.get('caveat64')
    if caveat is not None:
        caveat = utils.b64decode(caveat)

    return bakery.discharge(
        ctx,
        id=id,
        caveat=caveat,
        key=key,
        checker=checker,
        locator=locator,
    )
