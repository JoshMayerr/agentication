import json
import requests
import urllib.parse

from langchain_core.tools import tool

from generic_client import GenericClient

client = GenericClient(
    client_id='test-client',
    client_secret='test-secret'
)


def extract_tweet_info(response):
    if 'data' in response and 'user' in response['data'] and 'result' in response['data']['user']:
        user_result = response['data']['user']['result']
        trigger = False

        result = {
            'user': {},
            'tweets': []
        }

        if 'timeline_v2' in user_result and 'timeline' in user_result['timeline_v2']:
            timeline = user_result['timeline_v2']['timeline']
            if 'instructions' in timeline:
                for instruction in timeline['instructions']:
                    if instruction['type'] == 'TimelineAddEntries':
                        for entry in instruction['entries']:
                            if 'content' in entry and 'itemContent' in entry['content']:
                                item_content = entry['content']['itemContent']
                                if 'tweet_results' in item_content:
                                    tweet_result = item_content['tweet_results']['result']
                                    if trigger == False:
                                        result['user']["rest_id"] = tweet_result.get(
                                            'rest_id')
                                    full_text = None
                                    if 'note_tweet' in tweet_result and 'note_tweet_results' in tweet_result['note_tweet']:
                                        full_text = tweet_result['note_tweet']['note_tweet_results']['result'].get(
                                            'text')
                                    elif 'legacy' in tweet_result:
                                        full_text = tweet_result['legacy'].get(
                                            'full_text')

                                    if trigger == False:
                                        screen_name = tweet_result['core']['user_results']['result']['legacy'].get(
                                            'screen_name')
                                        result['user']['screen_name'] = screen_name
                                        trigger = True

                                    result['tweets'].append(full_text)

    return result


@tool
def get_id_for_username(username: str):
    """
    Get the Twitter ID for a given username.
    """

    url = "https://x.com/i/api/graphql/xmU6X_CKVnQ5lSrCbAmJsg/UserByScreenName?features=%7B%22hidden_profile_subscriptions_enabled%22%3Atrue%2C%22rweb_tipjar_consumption_enabled%22%3Atrue%2C%22responsive_web_graphql_exclude_directive_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22subscriptions_verification_info_is_identity_verified_enabled%22%3Atrue%2C%22subscriptions_verification_info_verified_since_enabled%22%3Atrue%2C%22highlights_tweets_tab_ui_enabled%22%3Atrue%2C%22responsive_web_twitter_article_notes_tab_enabled%22%3Atrue%2C%22subscriptions_feature_can_gift_premium%22%3Atrue%2C%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%7D&fieldToggles=%7B%22withAuxiliaryUserLabels%22%3Afalse%7D"

    # params = {"screen_name": "elonmusk", "withSafetyModeUserFields": True}
    variables = {
        "screen_name": username,
        "withSafetyModeUserFields": True
    }

    url = "https://x.com/i/api/graphql/xmU6X_CKVnQ5lSrCbAmJsg/UserByScreenName"
    encoded_variables = urllib.parse.quote(json.dumps(variables))
    query_params = f"variables={encoded_variables}&features=%7B%22hidden_profile_subscriptions_enabled%22%3Atrue%2C%22rweb_tipjar_consumption_enabled%22%3Atrue%2C%22responsive_web_graphql_exclude_directive_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22subscriptions_verification_info_is_identity_verified_enabled%22%3Atrue%2C%22subscriptions_verification_info_verified_since_enabled%22%3Atrue%2C%22highlights_tweets_tab_ui_enabled%22%3Atrue%2C%22responsive_web_twitter_article_notes_tab_enabled%22%3Atrue%2C%22subscriptions_feature_can_gift_premium%22%3Atrue%2C%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%7D&fieldToggles=%7B%22withAuxiliaryUserLabels%22%3Afalse%7D"

    url = f"{url}?{query_params}"

    token = client.get_token(host='x.com', scopes=[
                             "profile", "tweet.read"])

    response = client.make_request(url, method="GET", token=token)

    return response['data']['user']['result']['rest_id']


@tool
def get_recent_tweets(restId: str):
    """
    Get the recent tweets for a given user.
    """
    get_tweets_url = "https://x.com/i/api/graphql/-oADiDXCeko8ztc6Vvth5Q/UserTweets?variables=%7B%22userId%22%3A%2248008938%22%2C%22count%22%3A20%2C%22includePromotedContent%22%3Atrue%2C%22withQuickPromoteEligibilityTweetFields%22%3Atrue%2C%22withVoice%22%3Atrue%2C%22withV2Timeline%22%3Atrue%7D&features=%7B%22rweb_tipjar_consumption_enabled%22%3Atrue%2C%22responsive_web_graphql_exclude_directive_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22communities_web_enable_tweet_community_results_fetch%22%3Atrue%2C%22c9s_tweet_anatomy_moderator_badge_enabled%22%3Atrue%2C%22articles_preview_enabled%22%3Atrue%2C%22tweetypie_unmention_optimization_enabled%22%3Atrue%2C%22responsive_web_edit_tweet_api_enabled%22%3Atrue%2C%22graphql_is_translatable_rweb_tweet_is_translatable_enabled%22%3Atrue%2C%22view_counts_everywhere_api_enabled%22%3Atrue%2C%22longform_notetweets_consumption_enabled%22%3Atrue%2C%22responsive_web_twitter_article_tweet_consumption_enabled%22%3Atrue%2C%22tweet_awards_web_tipping_enabled%22%3Afalse%2C%22creator_subscriptions_quote_tweet_preview_enabled%22%3Afalse%2C%22freedom_of_speech_not_reach_fetch_enabled%22%3Atrue%2C%22standardized_nudges_misinfo%22%3Atrue%2C%22tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled%22%3Atrue%2C%22rweb_video_timestamps_enabled%22%3Atrue%2C%22longform_notetweets_rich_text_read_enabled%22%3Atrue%2C%22longform_notetweets_inline_media_enabled%22%3Atrue%2C%22responsive_web_enhance_cards_enabled%22%3Afalse%7D&fieldToggles=%7B%22withArticlePlainText%22%3Afalse%7D"

    params = {"userId": restId, "count": 20, "includePromotedContent": True,
              "withQuickPromoteEligibilityTweetFields": True, "withVoice": True, "withV2Timeline": True}

    # format the params as a query string
    query_params = "&".join([f"{k}={v}" for k, v in params.items()])
    get_tweets_url = f"{get_tweets_url}?{query_params}"

    token = client.get_token(host='x.com', scopes=[
                             "profile", "tweet.read"])

    response = client.make_request(
        get_tweets_url, method="GET", token=token)

    print(response)
    return extract_tweet_info(response)["tweets"]


@tool
def post_to_linkedin(content: str):
    """
    Given content for the post, post it to LinkedIn.
    """
    url = "https://www.linkedin.com/voyager/api/graphql?action=execute&queryId=voyagerContentcreationDashShares.5c3a8a34a002f744ca0dc6a295a1569c"

    payload = {
        "variables": {
            "post": {
                "allowedCommentersScope": "ALL",
                "intendedShareLifeCycleState": "PUBLISHED",
                "origin": "FEED",
                "visibilityDataUnion": {
                    "visibilityType": "ANYONE"
                },
                "commentary": {
                    "text": content,
                    "attributesV2": []
                }
            }
        },
        "queryId": "voyagerContentcreationDashShares.5c3a8a34a002f744ca0dc6a295a1569c",
        "includeWebMetadata": True
    }

    token = client.get_token(host='www.linkedin.com', scopes=[
                             'profile', 'connections'])

    response = client.make_request(
        url, method="POST", token=token, body=payload)

    return {"message": "Post successful"}
