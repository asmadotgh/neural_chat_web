const ps = new PerfectScrollbar('#chatlines-container', {suppressScrollX:true});
new PerfectScrollbar('#chatbotchoices', {suppressScrollX:true});
new PerfectScrollbar('#feedbackwindow', {suppressScrollX:true});
new PerfectScrollbar('#informedconsentcontent', {suppressScrollX:true});
new PerfectScrollbar('#review-chat-history', {suppressScrollX:true});


$( document ).ready(function() {

    var chatUUID = generateUUID();
    var chatbotid, chatbotname;
    var messageHistory = [];
    var chatCount = 0;

    setIsChatting(false);

    $(".consentbutton").click(function() {
        $("#informedconsent").hide();
        Cookies.set("consentcookie", 1);
        showTutorial();
    });

    if (! Cookies.get("consentcookie")) {
        $("#informedconsent").show();
    }

    $(".choice").click(function() {
        $("#robotchoices").hide();
        chatbotid = $(this).data("botid");
        chatbotname = $(this).data("name");
        $("#botname").html(chatbotname);

        $("#message").focus();
        setIsChatting(true);

        $("#chatbot_id").val(chatbotid);
        $("#chat_id").val(chatUUID);
        $("#loading").find(".user").text('[' + chatbotname + ']: ');

        if (window.STUDY_KEY == "index") {
            var indexPrompts = ["Hello! So, what’s on your mind?", "Hi! how are you feeling today?", "Hey! Tell me about your day."];
            var choice = indexPrompts[Math.floor(Math.random() * indexPrompts.length)];
            addChatLine(chatbotname, choice, null);

        }
    });

    if ($(".choice").length == 1) {
        $(".choice").click();
    }

    $('.input').keypress(function (e) {
        if (e.which == 13) {
            $('#submit').click();
            return false;
        }
    });

    $("#submit").click(function() {
        $("#message").focus();
        var message = $("#message").val();
        if (! message) {
            return false;
        }
        $("#message").val("");

        if (message.toLowerCase() == "quit" || message.toLowerCase() == "exit") {
            $(".close").click();
            return false;
        }


        messageHistory.push(message);
        messageHistory = lastFive(messageHistory);

        $("#submit").attr('disabled','disabled');
        $("#submit .loading").show();
        $("#submit .text").fadeTo(0, 0);
        $("#loading").show();

        addChatLine("User", message);
        chatCount += 1;

        var requestTime = new Date();

        $.ajax("/chat_message/", {
            type: "POST",
            url: "/chat_message/",
            dataType: "json",
            data: {message:message,
                chatbotID:chatbotid,
                chatID:chatUUID,
                studyKey:window.STUDY_KEY,
                timestamp:new Date().getTime(),
                messageHistory:JSON.stringify(messageHistory)
            },
            success: function(response) {

                var length = response.response_stripped.length;

                var botTypingDuration = (length * .04 + .15) * 1000 / 3;
                var realDuration = new Date() - requestTime;
                setTimeout(function() {
                    $("#submit").attr('disabled',null);
                    $("#submit .loading").hide();
                    $("#submit .text").fadeTo(0, 1);
                    $("#loading").hide();

                    messageHistory.push(response.response_stripped);
                    messageHistory = lastFive(messageHistory);

                    addChatLine(chatbotname, response.response, response.response_id);

                }, Math.max(0, botTypingDuration - realDuration));

            },
            error: function() {
                $("#submit").attr('disabled',null);
                $("#submit .loading").hide();
                $("#submit .text").fadeTo(0, 1);
                $("#loading").hide();

                var $messageLine = $('<div class="chatline"><span class="message error">[SERVER ERROR TRY AGAIN]</span></div>');
                $("#chatlines").append($messageLine);
                $("#chatlines").parent().scrollTop($("#chatlines").parent()[0].scrollHeight);
            }
        })
    })

    $(".close").click(function() {
        if (chatCount <3 ) {
            $("#chatrateconfirm").show();
            return;
        }
        $("#chatlines").clone().appendTo($("#review-chat-history"));

        $("#review-chat-history .chatline").each(function() {
            initVoteButtons($(this));
        })
        $("#chatrate").show();
    });

    $("#confirm-rate").click(function() {
        $("#chatrateconfirm").hide();
        setIsChatting(false);
        $("#chatratethanks").show();
    });

    $("#cancel-rate").click(function() {
        $("#chatrateconfirm").hide();
    });

    $("#rateform").submit(function(e) {
        var $form = $(this);
        e.stopPropagation();

        var valid = true;

        $form.find(".likert").each(function() {
            var $field = $(this);
            $field.removeClass("error");
            console.log($(this).find("input:checked"));
            if (! $(this).find("input:checked").val()) {
                $field.addClass("error");
                valid = false;
            }
        });

        if (valid) {
            $.ajax($form.attr("action"),
                {
                    type:"POST",
                    data: $form.serialize(),
                    dataType: "json",
                    error: function() {
                        alert("There was an error submitting your rating. Please try again later!");
                    },
                    success: function(response) {
                        setIsChatting(false);
                        $("#chatrate").hide();

                        if (response.mturk_code) {
                            $("#mturk-code").html(response.mturk_code);
                        } else {
                            $("#mturk-wrapper").hide();
                        }

                        $("#chatratethanks").show();
                    }
                });
        }

        return false;
    })

    $("#confirm-close").click(function() {
        window.location = window.location;
    });

    $("#tutorial .tutorialpage .button").click(function() {
        $("#tutorial .tutorialpage").hide();
        var $next = $(this).parents(".tutorialpage").next();
        if ($next.length > 0) {
            $next.show();
        } else {
            $("#tutorial").hide();
        }
    });

});

function showTutorial() {
    $("#tutorial").show();
    $("#tutorial .tutorialpage").hide();
    $("#tutorial .tutorialpage:nth-child(1)").show();
}


function setIsChatting(isChatting) {
    window.isChatting = isChatting;
    if (isChatting) {
        $(window).bind('beforeunload', function(){
            return "Please close your chat session and rate it before leaving.";
        });
    } else {
        $(window).unbind('beforeunload');
    }
}

function addChatLine(username, message, responseID) {
    var $messageLine = $('<div class="chatline"><span class="votes"><span class="upvote vote"></span><span class="downvote vote"></span></span><span class="user"></span><span class="message"></span></div>');
    $messageLine.find(".message").text(message);
    $messageLine.find(".user").text('[' + username + ']: ');
    $messageLine.data("responseid", responseID);
    $messageLine.attr("data-responseid", responseID);
    if (responseID) {
        initVoteButtons($messageLine);
    } else {
        $messageLine.find(".votes").empty();
    }
    $("#chatlines").append($messageLine);
    ps.update();
    $("#chatlines-container").scrollTop($("#chatlines-container")[0].scrollHeight);
}

function initVoteButtons($messageLine) {
    var responseID = $messageLine.data("responseid");

    $messageLine.find(".upvote").click(function() {
        rateResponse(1, responseID, true);
    });
    $messageLine.find(".downvote").click(function() {
        rateResponse(-1, responseID, false);
    });
}

function rateResponse(rating, responseID, isUp) {
    $.ajax("/rate_chat_response/", {
        type:"post",
        dataType:"json",
        data:{
            response_id:responseID,
            rating:rating,
        },
        success: function(response) {
            var $voteButtons = $(".chatline[data-responseID='" + responseID + "'] .vote");
            $voteButtons.removeClass("active");
            if (response.make_vote_active) {
                $voteButtons.filter(isUp ? ".upvote" : ".downvote").addClass("active");
            }
        },
    })
}

function generateUUID() {
    var d = new Date().getTime();
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });
    return uuid;
}

function lastFive(arr) {
    return arr.slice(Math.max(arr.length - 5, 0))
}
