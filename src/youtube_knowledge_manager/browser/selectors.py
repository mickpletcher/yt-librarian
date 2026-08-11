class Selectors:
    PLAYLIST_CARDS = "yt-lockup-view-model"
    PLAYLIST_CARD_LINK = "a[href*='/playlist?list=']"
    PLAYLIST_CARD_TITLE = ".ytLockupMetadataViewModelTextContainer h3 a"
    PLAYLIST_CARD_COUNT = ".ytBadgeShapeText, ytd-thumbnail-overlay-side-panel-renderer #text"

    PLAYLIST_ITEMS = (
        "ytd-two-column-browse-results-renderer #primary ytd-playlist-video-renderer, "
        "ytd-two-column-browse-results-renderer #primary yt-lockup-view-model"
    )
    PLAYLIST_VIDEO_COUNT = (
        "yt-formatted-string.style-scope.ytd-playlist-sidebar-primary-info-renderer, "
        "yt-formatted-string.byline-item.style-scope.ytd-playlist-byline-renderer"
    )
    VIDEO_LINK = "a#video-title, a.ytLockupViewModelContentImage"
    PLAYLIST_TITLE = "a#video-title, .ytLockupMetadataViewModelTextContainer h3 a"
    CHANNEL_LINK = "ytd-channel-name a, yt-content-metadata-view-model a"
    THUMBNAIL = "ytd-thumbnail img, yt-thumbnail-view-model img"
    DURATION = "ytd-thumbnail-overlay-time-status-renderer span, .ytBadgeShapeText"
    UNAVAILABLE = "#unplayableText, ytd-badge-supported-renderer"
    LIBRARY_CONTINUATION = "ytd-continuation-item-renderer, yt-continuation-item-view-model"
    PLAYLIST_CONTINUATION = (
        "ytd-two-column-browse-results-renderer #primary ytd-continuation-item-renderer, "
        "ytd-two-column-browse-results-renderer #primary yt-continuation-item-view-model"
    )
    PLAYLIST_EMPTY_STATE = (
        "ytd-message-renderer:has-text('No videos'), "
        "yt-page-header-view-model:has-text('No videos')"
    )

    VIDEO_TITLE = "h1.ytd-watch-metadata yt-formatted-string"
    VIDEO_DESCRIPTION = "#description-inline-expander"
    VIDEO_CHANNEL = "#owner ytd-channel-name a"
    SHOW_MORE_BUTTON = "#expand"
    MORE_ACTIONS_BUTTON = "button[aria-label*='More actions'], #button-shape button"
    TRANSCRIPT_MENU_ITEM = "ytd-menu-service-item-renderer:has-text('Show transcript')"
    TRANSCRIPT_SEGMENT = "ytd-transcript-segment-renderer"
    TRANSCRIPT_TEXT = ".segment-text"
    TRANSCRIPT_TIME = ".segment-timestamp"

    SAVE_BUTTON = "button[aria-label*='Save to playlist'], button:has-text('Save')"
    PLAYLIST_DIALOG = "ytd-add-to-playlist-renderer, tp-yt-paper-dialog"
    PLAYLIST_OPTION = "ytd-playlist-add-to-option-renderer"
    PLAYLIST_OPTION_TITLE = "#label"
    PLAYLIST_OPTION_CHECKBOX = "tp-yt-paper-checkbox"

    CAPTCHA = "iframe[src*='recaptcha'], #captcha-form, [aria-label*='CAPTCHA']"
    CONSENT_DIALOG = "form[action*='consent'], [aria-label*='consent'], #dialog:has-text('cookies')"
    LOGIN_FORM = (
        "form[action*='signin'], input[type='email'], input[type='password'], "
        "a[aria-label='Sign in'], a[href*='accounts.google.com/ServiceLogin']"
    )
    SECURITY_PROMPT = "[data-challengeindex], form[action*='challenge']"


SECURITY_URL_PARTS = (
    "accounts.google.com/signin",
    "accounts.google.com/v3/signin",
    "accounts.google.com/challenge",
    "youtube.com/oops",
)
