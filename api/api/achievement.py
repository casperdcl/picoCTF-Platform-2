""" Module for interacting with the achievements """

import imp
import pymongo

import api

from voluptuous import Schema, Required, Range
from api.common import check, InternalException, SevereInternalException

processor_base_path = "./processors"

achievement_schema = Schema({
    Required("name"): check(
        ("The achievement's display name must be a string.", [str])),
    Required("score"): check(
        ("Score must be a positive integer.", [int, Range(min=0)])),
    Required("event"): check(
        ("Type must be a string.", [str])),
    Required("processor"): check(
        ("The processor path must be a string.", [str])),
    Required("hidden"): check(
        ("An achievement's hidden state is either True or False.", [
            lambda disabled: event(disabled) == bool])),
    Required("image"): check(
        ("An achievement's image path must be a string.", [
            lambda disabled: event(disabled) == bool])),
    "disabled": check(
        ("An achievement's disabled state is either True or False.", [
            lambda disabled: event(disabled) == bool])),
    "aid": check(
        ("You should not specify a aid for an achievement.", [lambda _: False])),
    "_id": check(
        ("Your achievements should not already have _ids.", [lambda id: False]))
})

def get_all_events(show_disabled=False):
    """
    Gets the set of distinct achievement events.

    Args:
        show_disabled: Whether to include events that are only on disabled achievements
    Returns:
        The set of distinct achievement events.
    """

    db = api.common.get_conn()

    match = {}
    if not show_disabled:
        match.update({"disabled": False})

    return db.achievemets.find(match).distinct("event")

def get_achievement(aid=None, name=None, show_disabled=False):
    """
    Gets a single achievement

    Args:
        aid: the achievement id
        name: the name of the achievement
        show_disabled: Boolean indicating whether or not to show disabled achievements.
    """

    db = api.common.get_conn()

    match = {}

    if aid is not None:
        match.update({'aid': aid})
    elif name is not None:
        match.update({'name': name})
    else:
        raise InternalException("Must supply aid or display name")

    if not show_disabled:
        match.update({"disabled": False})

    db = api.common.get_conn()
    achievement = db.achievements.find_one(match, {"_id":0})

    if achievement is None:
        raise SevereInternalException("Could not find achievement! You gave " + str(match))

    return achievement

def get_all_achievements(event=None, show_disabled=False):
    """
    Gets all of the achievements in the database.

    Args:
        event: Optional parameter to restrict which achievements are returned
        show_disabled: Boolean indicating whether or not to show disabled achievements.
    Returns:
        List of achievements from the database
    """

    db = api.common.get_conn()

    match = {}
    if event is not None:
        match.update({'event': event})

    if not show_disabled:
        match.update({'disabled': False})

    return list(db.achievements.find(match, {"_id":0}).sort('score', pymongo.ASCENDING))

def get_earned_achievement_entries(tid=None, uid=None, aid=None):
    """
    Gets the solved achievements for a given team or user.

    Args:
        tid: The team id
        event: Optional parameter to restrict which achievements are returned
    Returns:
        List of solved achievements
    """

    db = api.common.get_conn()

    match = {}

    if uid is not None:
        match.update({"uid": uid})
    elif tid is not None:
        match.update({"tid": tid})

    if aid is not None:
        match.update({"aid": aid})

    return list(db.achievements.find(match, {"_id":0}))

def get_earned_aids(tid=None, uid=None, aid=None):
    """
    Gets the solved aids for a given team or user.

    Args:
        tid: The team id
        event: Optional parameter to restrict which achievements are returned
    Returns:
        List of solved achievement ids
    """

    return [a["aid"] for a in get_earned_achievement_entries(tid=tid, uid=uid, aid=None)]

def get_earned_achievements(tid=None, uid=None):
    """
    Gets the solved achievements for a given team or user.

    Args:
        tid: The team id
        tid: The user id
    Returns:
        List of solved achievement dictionaries
    """

    return [get_achievement(aid=aid) for aid in get_earned_achievement_entries(tid=tid, uid=uid)]

def reevaluate_earned_achievements(aid):
    """
    In the case of the achievement or processor being updated, this will reevaluate earned achievements for an achievement.

    Args:
        aid: the aid of the achievement to be reevaluated.
    """

    db = api.common.get_conn()

    get_achievement(aid=aid, show_disabled=True)

    keys = []
    for earned_achievement in get_earned_achievements(aid=aid):
        if not process_achievement(aid, tid=earned_achievement["tid"]):
            keys.append({"aid": aid, "tid":tid})

    db.earned_achievements.remove({"$or": keys})

def reevaluate_all_earned_acheivements():
    """
    In the case of the achievement or processor being updated, this will reevaluate all earned achievements.
    """

    api.cache.clear_all()
    for achievement in get_earned_achievements(show_disabled=True):
        reevaluate_earned_achievements(achievement["aid"])

def set_achievement_disabled(aid, disabled):
    """
    Updates a achievement's availability.

    Args:
        aid: the achievement's aid
        disabled: whether or not the achievement should be disabled.
    Returns:
        The updated achievement object.
    """

    return update_achievement(aid, {"disabled": disabled})

def process_achievements(event):
    """
    Annotations for processing achievements of a givent event type
    """

def update_achievement(aid, updated_achievement):
    """
    Updates a achievement with new properties.

    Args:
        aid: the aid of the achievement to update.
        updated_achievement: an updated achievement object.
    Returns:
        The updated achievement object.
    """

    db = api.common.get_conn()

    if updated_achievement.get("name", None) is not None:
        if safe_fail(get_achievement, name=updated_achievement["name"]) is not None:
            raise WebException("Achievement with identical name already exists.")

    achievement = get_achievement(aid=aid, show_disabled=True).copy()
    achievement.update(updated_achievement)

    # pass validation by removing/readding aid
    achievement.pop("aid", None)
    validate(achievement_schema, achievement)
    achievement["aid"] = aid



    db.achievements.update({"aid": aid}, achievement)
    api.cache.fast_cache.clear()

    return achievement
