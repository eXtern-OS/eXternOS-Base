'use strict';
/******************************************************************************
 ** Copyright (c) 2017 Sujaykumar.Hublikar <sujaykumar6390@gmail.com>
 **
 ** Licensed under the Apache License, Version 2.0 (the "License");
 ** you may not use this file except in compliance with the License.
 ** You may obtain a copy of the License at
 **
 **       http://www.apache.org/licenses/LICENSE-2.0
 **
 ** Unless required by applicable law or agreed to in writing, software
 ** distributed under the License is distributed on an "AS IS" BASIS,
 ** WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 ** See the License for the specific language governing permissions and
 ** limitations under the License.
 ******************************************************************************/

// Global Variables
var _currentUserId = 0;
var _currentUserSessionId = 0;
var _snackbar;
var _defaultUserImage = "images/user.png";

$(document).ready(function () {
    // enable tooltip
    //$('[data-toggle="tooltip"]').tooltip();
    window.debugMode = window.lightdm === undefined;
    var manager = new ThemeManager();
    _snackbar = $('#snackbar-host').snackbarInit();
	$("#mainContent").removeClass("hiddenOpacity");
});

function ThemeManager() {
    this.init();
    //console.log('LightDM: ', window.lightdm);
}

ThemeManager.prototype = {
    _days: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
    _months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'],
    init: function () {
        if (window.debugMode) {
            //init Mock Data
            initMockData();
        }
        this.initAlert();
        this.initSnackBar();
        this.initTime();
        this.initPassowrdInput();
        this.initButtons();
        this.initThemeData();
        //this.overrideAlert();
    },
    overrideAlert: function () {
        var _alert = window.alert;
        window.alert = function (message, old) {
            if (old) {
                _alert(message);
                return;
            }
            _snackbar.snackbar(message);
        }
    },
    initSnackBar: function () {
        (function ($) {
            $.fn.snackbarInit = function () {
                $(this).css('position', 'fixed');
                $(this).css('width', '100%');
                $(this).css('bottom', '0');
                $(this).css('max-height', '300px');
                $(this).css('scroll', 'auto');
                return this;
            };
            $.fn.snackbar = function (message, actionTitle, callback) {
                var _sb_container = $('<div class="snackbar-container"></div>');
                var _sb_content = $('<span class="snackbar-content disableSelector">SNACKBAR</span>');
                var _sb_action = '<span class="snackbar-action">ACTION</span>';

                $(_sb_content).html(message);
                if (actionTitle) {
                    $(_sb_action).html(actionTitle);
                    $(_sb_action).click(function () {
                        callback();
                    });
                    $(_sb_container).append(_sb_action);
                }

                $(_sb_container).append(_sb_content);
                $(this).append(_sb_container);

                var snackbar = this;
                $(this).find('.snackbar-container').addClass('show').delay(2500).queue(function (next) {
                    $(snackbar).find('.snackbar-container').first().remove();
                    next();
                });
                return this;
            };
        }(jQuery));
    },
    initAlert: function () {
        $("#alert").hide();
        $("#alert .btn-negative").click(function () {
            $("#alert").hide();
        });
    },
    initThemeData: function () {
	if (lightdm.hostname == "extern")
		$("#hostname").html("eXtern OS");
	else
        	$("#hostname").html(lightdm.hostname);

        this.addSessions();
        this.addUsers();
        this.updateUserInfo();
    },
    initTime: function () {
        var manager = this;
        this.updateTime();
        setInterval(function () {
            manager.updateTime();
        }, 1000 * 30);
    },
    initPassowrdInput: function () {
        var manager = this;
        $('.input-password button').click(function () {
            $(this).find('i').toggleClass('fa-eye');
            $(this).find('i').toggleClass('fa-eye-slash');
            var input = $(this).parent().find('input');
            $(input).attr('type', ($(input).attr('type') === "text") ? "password" : "text");
            $(this).attr('title', ($(input).attr('type') === "password") ? "show password" : "hide password");
        });

        $('.input-password input').keypress(function (e) {
            if (e.keyCode == '13') {
                manager.authUser($('.input-password input').val());
            }
        });
    },
    initButtons: function () {
        var manager = this;
        $('#login-current-session').click(function () {
            $("#login").hide();
            manager.showUserSessions();
        });

        $('#login-user-img img').click(function () {
            $("#login").hide();
            manager.showUsers();
        });

        // Control Buttons
        var manager = this;
        // ShutDown Button
        if(!window.lightdm.can_shutdown) $('#control-shutdown').hide();
        $('#control-shutdown').click(function () {
            manager.createAlert("Shutdown", "Do you Want to shutdown System?", function () {
                lightdm.shutdown();
            });
        });
        // Hibernate Button
        if(!window.lightdm.can_hibernate) $('#control-hibernate').hide();
        $('#control-hibernate').click(function () {
            manager.createAlert("Hibernate", "Do you Want to Hibernate System?", function () {
                lightdm.hibernate();
            });
        });
        // Suspend Button
        if(!window.lightdm.can_suspend) $('#control-suspend').hide();
        $('#control-suspend').click(function () {
            manager.createAlert("Suspend", "Do you Want to Suspend System?", function () {
                lightdm.suspend();
            });
        });
        // Restart Button
        if(!window.lightdm.can_restart) $('#control-restart').hide();
        $('#control-restart').click(function () {
            manager.createAlert("Restart", "Do you Want to Restart System?", function () {
                lightdm.restart();
            });
        });
    },
    authUser: function (password) {
        loginUser(lightdm.users[_currentUserId].name, password, function () {
            // SUCCESS
            //alert("SUCCESS");
            start(lightdm.sessions[_currentUserSessionId].key);
        }, function (message) {
            //ERROR
            $('.input-password').addClass('password-invalid').delay(200).queue(function (next) {
                $(this).removeClass('password-invalid');
                next();
            });
        });
    },
    updateUserInfo: function () {
        $("#login .name").html(this.getUserInfo.dispalyName());
        $("#login .username").html("( " + this.getUserInfo.userName() + " )");
	if (lightdm.sessions.length > 1)
		$("#login-current-session").removeClass("hidden");

        $("#login-session-text").html(this.getUserInfo.userSession());
        $('#login-user-img img').attr('src', this.getUserInfo.userImage());
    },
    clearPasswordInput: function () {
        $('.input-password input').val('');
    },
    updateSessionId: function (pos) {
        if (lightdm.users[pos].session === null) return; // retrun if no default session is set
        var _session = lightdm.users[pos].session.toLowerCase();
        _currentUserSessionId = lightdm.sessions.map(function (e) {
            return e.key;
        }).indexOf(_session);
    },
    getUserInfo: {
        userName: function () {
            return lightdm.users[_currentUserId].username;
        },
        dispalyName: function () {
            return lightdm.users[_currentUserId].display_name;
        },
        userSession: function () {
            return lightdm.sessions[_currentUserSessionId].name;
        },
        userImage: function () {
            return (lightdm.users[_currentUserId].image !== null) ? lightdm.users[_currentUserId].image : _defaultUserImage;
        }
    },
    createAlert: function (title, message, callback) {
        $("#alert-title").html(title);
        $("#alert-message").html(message);
        $("#alert .btn-positive").click(function () {
            callback();
            $("#alert").hide();
        });
        $("#alert").show();
    },
    updateTime: function () {
        //console.log("TICK TOK!");
        var _date = new Date();
        $('#clock-date-day').html(this._days[_date.getDay()]);
        $('#clock-date-date').html(_date.getDate() + ' ' + this._months[_date.getMonth()]);
        $('#clock-time-hr').html(_date.getHours());
        $('#clock-time-min').html((_date.getMinutes() < 10 ? '0' : '') + _date.getMinutes());
    },
    addSessions: function () {
        for (var i = 0; i < lightdm.sessions.length; i++) {
            var session = lightdm.sessions[i];
            this.addUserSessionButton(session, i);
        }
    },
    addUserSessionButton: function (session, pos) {
        var manager = this;
        var sessionBtn = new $('#dump-sessionButton').clone();
        $(sessionBtn).attr('id', '');
        $(sessionBtn).attr('data-session-key', session.key);
        $(sessionBtn).attr('title', session.comment);
        $(sessionBtn).find('span').html(session.name);
        $(sessionBtn).click(function () {
            _currentUserSessionId = pos;
            manager.updateUserInfo();
            $("#login").show();
            $("#login-sessions").hide();
            lightdm.cancel_authentication();
        });
        $('#login-sessions').append(sessionBtn);
    },
    showUserSessions: function () {
        $("#login-sessions button").removeClass('active');
        $("#login-sessions button").eq(_currentUserSessionId).addClass('active');
        $("#login-sessions").show();
    },
    addUsers: function () {
        for (var i = 0; i < lightdm.users.length; i++) {
            var user = lightdm.users[i];
            this.addUserButton(user, i);
        }
    },
    addUserButton: function (user, pos) {
        var manager = this;
        var userBtn = new $('#dump-userButton').clone();
        $(userBtn).attr('id', '');
        $(userBtn).find('span.name').html(user.display_name);
        $(userBtn).find('span.username').html(user.name);
        $(userBtn).find('img').attr('src', (user.image !== null) ? user.image : _defaultUserImage);
        $(userBtn).click(function () {
            $("#login").show();
            $("#login-users").hide();
            _currentUserId = pos;
            manager.clearPasswordInput();
            manager.updateSessionId(pos);
            manager.updateUserInfo();
        });
        $('#login-users').append(userBtn);
    },
    showUsers: function () {
        $("#login-users button").removeClass('active');
        $("#login-users button").eq(_currentUserId).addClass('active');
        $("#login-users").show();
    }
};

// MOCK.js from https://github.com/Antergos/web-greeter/blob/master/themes/_vendor/js/mock.js
// MOCK data for LIGHTDM if DEBUG = true

function initMockData() {
    window.lightdm = {
        greeter: {
            default_values: {
                string: () => '',
                int: () => 0,
                bool: () => false,
                list: () => [],
                'null': () => null
            },
            hostname: 'Mock Greeter',
            properties: {
                string: ['authentication_user', 'autologin_user', 'default_session', 'hostname', 'num_users'],
                int: ['autologin_timeout'],
                bool: [
                    'autologin_guest', 'can_hibernate', 'can_restart', 'can_shutdown', 'can_suspend',
                    'has_guest_account', 'hide_users', 'in_authentication', 'is_authenticated',
                    'lock_hint', 'select_guest_hint', 'select_user_hint'
                ],
                list: ['languages', 'layouts', 'sessions', 'users'],
                'null': ['language', 'layout']
            }
        },
        languages: [{
                name: 'English',
                code: 'en_US.utf8',
                territory: 'USA'
            },
            {
                name: 'Catalan',
                code: 'ca_ES.utf8',
                territory: 'Spain'
            },
            {
                name: 'French',
                code: 'fr_FR.utf8',
                territory: 'France'
            }
        ],
        layouts: [{
                name: 'us',
                short_description: 'en',
                description: 'English (US)'
            },
            {
                name: 'at',
                short_description: 'de',
                description: 'German (Austria)'
            },
            {
                name: 'us rus',
                short_description: 'ru',
                description: 'Russian (US, phonetic)'
            }
        ],
        sessions: [{
                key: 'gnome',
                name: 'GNOME',
                comment: 'This session logs you into GNOME'
            },
            {
                key: 'cinnamon',
                name: 'Cinnamon',
                comment: 'This session logs you into Cinnamon'
            },
            {
                key: 'plasma',
                name: 'Plasma',
                comment: 'Plasma by KDE'
            },
            {
                key: 'mate',
                name: 'MATE',
                comment: 'This session logs you into MATE'
            },
            {
                key: 'openbox',
                name: 'Openbox',
                comment: 'This session logs you into Openbox'
            }
        ],
        users: [{
                display_name: 'Clark Kent',
                language: null,
                layout: null,
                //image: '/usr/share/lightdm-webkit/themes/antergos/img/antergos-logo-user',
                image: 'images/mockUser1.png',
                home_directory: '/home/superman',
                username: 'superman',
                logged_in: false,
                session: 'gnome',

                name: 'superman',
                real_name: 'Clark Kent'
            },
            {
                display_name: 'Bruce Wayne',
                language: null,
                layout: null,
                //image: '/usr/share/lightdm-webkit/themes/antergos/img/antergos-logo-user',
                image: 'images/mockUser2.png',
                home_directory: '/home/batman',
                username: 'batman',
                logged_in: false,
                session: 'cinnamon',

                name: 'batman',
                real_name: 'Bruce Wayne'
            },
            {
                display_name: 'Peter Parker',
                language: null,
                layout: null,
                //image: '/usr/share/lightdm-webkit/themes/antergos/img/antergos-logo-user',
                image: 'images/mockUser3.png',
                home_directory: '/home/spiderman',
                username: 'spiderman',
                logged_in: false,
                session: 'MATE',

                name: 'spiderman',
                real_name: 'Peter Parker'
            }
        ]
    };

    lightdm.provide_secret = function (secret) {
        if (typeof lightdm._username == 'undefined' || !lightdm._username) {
            throw "must call start_authentication first"
        }
        _lightdm_mock_check_argument_length(arguments, 1);
        var user = _lightdm_mock_get_user(lightdm.username);

        if (!user && secret == lightdm._username) {
            lightdm.is_authenticated = true;
            lightdm.authentication_user = user;
        } else {
            lightdm.is_authenticated = false;
            lightdm.authentication_user = null;
            lightdm._username = null;
        }
        authentication_complete();
    };

    lightdm.start_authentication = function (username) {
        if ('undefined' === typeof username) {
            show_prompt("Username?", 'text');
            lightdm.awaiting_username = true;
            return;
        }
        _lightdm_mock_check_argument_length(arguments, 1);
        if (lightdm._username) {
            throw "Already authenticating!";
        }
        var user = _lightdm_mock_get_user(username);
        if (!user) {
            show_error(username + " is an invalid user");
        }
        lightdm._username = username;
        show_prompt("Password: ");
    };

    lightdm.cancel_authentication = function () {
        _lightdm_mock_check_argument_length(arguments, 0);
        if (!lightdm._username) {
            console.log("we are not authenticating");
        }
        lightdm._username = null;
    };

    lightdm.suspend = function () {
        alert("System Suspended. Bye Bye");
        //_snackbar.show("System Suspended. Bye Bye");
        document.location.reload(true);
    };

    lightdm.hibernate = function () {
        alert("System Hibernated. Bye Bye");
        document.location.reload(true);
    };

    lightdm.restart = function () {
        alert("System restart. Bye Bye");
        document.location.reload(true);
    };

    lightdm.shutdown = function () {
        alert("System Shutdown. Bye Bye");
        document.location.reload(true);
    };

    lightdm.login = function (user, session) {
        _lightdm_mock_check_argument_length(arguments, 2);
        if (!lightdm.is_authenticated) {
            throw "The system is not authenticated";
        }
        if (user !== lightdm.authentication_user) {
            throw "this user is not authenticated";
        }
        alert("logged in successfully!!\n\n Session: " + session + "\n\nUser: " + lightdm._username);
        document.location.reload(true);
    };

    lightdm.authenticate = function (session) {
        lightdm.login(null, session);
    };

    lightdm.respond = function (response) {
        if (true === lightdm.awaiting_username) {
            lightdm.awaiting_username = false;
            lightdm.start_authentication(response);
        } else {
            lightdm.provide_secret(response);
        }
    };

    lightdm.start_session_sync = function () {
        lightdm.login(null, null);
    };

    if (lightdm.timed_login_delay > 0) {
        setTimeout(function () {
            if (!lightdm._timed_login_cancelled()) {
                timed_login();
            }
        }, lightdm.timed_login_delay);
    }

    var config = {},
        greeterutil = {};

    config.get_str = function (section, key) {
        var branding = {
            logo: 'img/antergos.png',
            user_logo: 'ing/antergos-logo-user.png',
            background_images: '/usr/share/antergos/wallpapers'
        };
        if ('branding' === section) {
            return branding[key];
        }
    };
    config.get_bool = function (section, key) {
        return true;
    };


    greeterutil.dirlist = function (directory) {
        if ('/usr/share/antergos/wallpapers' === directory) {
            return ['/usr/share/antergos/wallpapers/83II_by_bo0xVn.jpg', '/usr/share/antergos/wallpapers/antergos-wallpaper.png', '/usr/share/antergos/wallpapers/as_time_goes_by____by_moskanon-d5dgvt8.jpg', '/usr/share/antergos/wallpapers/autumn_hike___plant_details_by_aoiban-d5l7y83.jpg', '/usr/share/antergos/wallpapers/blossom_by_snipes2.jpg', '/usr/share/antergos/wallpapers/c65sk3mshowxrtlljbvh.jpg', '/usr/share/antergos/wallpapers/early_morning_by_kylekc.jpg', '/usr/share/antergos/wallpapers/extinction_by_signcropstealer-d5j4y84.jpg', '/usr/share/antergos/wallpapers/field_by_stevenfields-d59ap2i.jpg', '/usr/share/antergos/wallpapers/Grass_by_masha_darkelf666.jpg', '/usr/share/antergos/wallpapers/Grass_Fullscreen.jpg', '/usr/share/antergos/wallpapers/humble_by_splendidofsun-d5g47hb.jpg', '/usr/share/antergos/wallpapers/In_the_Grass.jpg', '/usr/share/antergos/wallpapers/morning_light.jpg', '/usr/share/antergos/wallpapers/Nautilus_Fullscreen.jpg', '/usr/share/antergos/wallpapers/nikon_d40.jpg', '/usr/share/antergos/wallpapers/sky_full_of_stars.jpg', '/usr/share/antergos/wallpapers/solely_by_stevenfields.jpg', '/usr/share/antergos/wallpapers/the_world_inside_my_lens__by_moskanon-d5fsiqs.jpg', '/usr/share/antergos/wallpapers/white_line_by_snipes2.jpg']
        }
    }

    function _lightdm_mock_check_argument_length(args, length) {
        if (args.length != length) {
            throw "incorrect number of arguments in function call";
        }
    }

    function _lightdm_mock_get_user(username) {
        var user = null;
        for (var i = 0; i < lightdm.users.length; ++i) {
            if (lightdm.users[i].name == username) {
                user = lightdm.users[i];
                break;
            }
        }
        return user;
    }
}

// AUTH SECTION for lightDM from @Litarvan Theme

var _password;
var _sucessCallback; // Callback for SUCCESS during auth
var _errorCallback; // Callback for ERROR during auth

function loginUser(username, pass, success, error) {
    _password = pass;
    _sucessCallback = success;
    _errorCallback = error;
    lightdm.start_authentication(username);
}

function start(desktop) {
    lightdm.login(lightdm.authentication_user, desktop);
}

function authentication_complete() {
    if (lightdm.is_authenticated) {
	$("#mainContent").addClass("hiddenOpacity");
	setTimeout(function () {
            _sucessCallback();
        }, 1000);
    } else {
        lightdm.cancel_authentication();
        _errorCallback("Invalid Password");
    }
}

function show_prompt(text, type) {
    //console.log('text.startsWith("Password: "): ' + text.startsWith("Password: "));
    if (text.startsWith("Password: ")) {
        lightdm.provide_secret(_password);
    }
}

function show_error(message) {
    _errorCallback(message);
}
