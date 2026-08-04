class Selectors:
    PLAYLIST_ITEMS = "ytd-playlist-video-renderer"
    VIDEO_LINK = "a#video-title"
    CHANNEL_LINK = "ytd-channel-name a"
    THUMBNAIL = "ytd-thumbnail img"
    DURATION = "ytd-thumbnail-overlay-time-status-renderer span"
    UNAVAILABLE = "#unplayableText, ytd-badge-supported-renderer"
    PLAYLIST_CONTINUATION = "ytd-continuation-item-renderer"

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
    LOGIN_FORM = "form[action*='signin'], input[type='email'], input[type='password']"
    SECURITY_PROMPT = "[data-challengeindex], form[action*='challenge']"


SECURITY_URL_PARTS = (
    "accounts.google.com/signin",
    "accounts.google.com/v3/signin",
    "accounts.google.com/challenge",
    "youtube.com/oops",
)
