/**
 * EduClaw media panel: Video.js v10 minimal UI integration.
 */

const DEMO_VIDEO =
  'https://stream.mux.com/BV3YZtogl89mg9VcNBhhnHm02Y34zI1nlMuMQfAbl3dM/highest.mp4';
const DEMO_POSTER =
  'https://image.mux.com/BV3YZtogl89mg9VcNBhhnHm02Y34zI1nlMuMQfAbl3dM/thumbnail.webp';
const DEMO_SUBTITLES = '/static/demo-lecture.vtt';

const LEARNING_RATES = [0.5, 0.75, 1, 1.25, 1.5, 2, 3, 4, 5, 6, 7, 8];

let captionBlobUrl = null;

function $(id) {
  return document.getElementById(id);
}

function hide(el) {
  if (el) el.classList.add('hidden');
}

function show(el) {
  if (el) el.classList.remove('hidden');
}

function srtToVtt(srt) {
  const body = srt
    .replace(/\r\n/g, '\n')
    .replace(/^\uFEFF/, '')
    .trim();
  const cues = body.replace(/(\d{2}:\d{2}:\d{2}),(\d{3})/g, '$1.$2');
  return cues.startsWith('WEBVTT') ? cues : `WEBVTT\n\n${cues}`;
}

function subtitleUrlFromVideoUrl(videoUrl) {
  if (!videoUrl) return null;
  const base = videoUrl.replace(/\/[^/]+$/, '');
  const name = videoUrl.split('/').pop() || '';
  if (/\.mp4$/i.test(name)) {
    return `${base}/subtitles.srt`;
  }
  return null;
}

async function fetchCaptionVtt(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Caption fetch failed: ${res.status}`);
  const text = await res.text();
  const vtt = url.toLowerCase().endsWith('.srt') ? srtToVtt(text) : text;
  return URL.createObjectURL(new Blob([vtt], { type: 'text/vtt' }));
}

function revokeCaptionBlob() {
  if (captionBlobUrl) {
    URL.revokeObjectURL(captionBlobUrl);
    captionBlobUrl = null;
  }
}

async function attachCaptions(videoEl, subtitlesUrl) {
  revokeCaptionBlob();
  videoEl.querySelectorAll('track[data-educlaw-caption]').forEach((t) => t.remove());

  if (!subtitlesUrl) return;

  try {
    captionBlobUrl = await fetchCaptionVtt(subtitlesUrl);
    const track = document.createElement('track');
    track.kind = 'captions';
    track.srclang = 'en';
    track.label = 'English';
    track.src = captionBlobUrl;
    track.default = true;
    track.dataset.educlawCaption = '1';
    videoEl.appendChild(track);
    track.track.mode = 'showing';
  } catch (err) {
    console.warn('[EduClawMedia] captions unavailable:', err);
  }
}

function patchLearningRates(playerEl) {
  const tryPatch = () => {
    const store = playerEl?.store;
    if (store?.$state?.patch) {
      store.$state.patch({ playbackRates: LEARNING_RATES });
      return true;
    }
    return false;
  };
  if (tryPatch()) return;
  const deadline = Date.now() + 5000;
  const timer = setInterval(() => {
    if (tryPatch() || Date.now() > deadline) clearInterval(timer);
  }, 50);
}

class EduclawLearningRates extends HTMLElement {
  connectedCallback() {
    const player = this.closest('video-player');
    if (player) patchLearningRates(player);
  }
}

if (!customElements.get('educlaw-learning-rates')) {
  customElements.define('educlaw-learning-rates', EduclawLearningRates);
}

function getVideoEl() {
  return $('educlaw-video');
}

function getPlayerEl() {
  return document.querySelector('#video-player-host video-player');
}

function pauseVideo() {
  const video = getVideoEl();
  if (video && !video.paused) video.pause();
}

function setPoster(videoEl, posterUrl) {
  const posterImg = document.querySelector('#video-player-host media-poster img');
  if (posterImg && posterUrl) posterImg.src = posterUrl;
  else if (posterImg && !posterUrl) posterImg.removeAttribute('src');
  if (videoEl && posterUrl) videoEl.poster = posterUrl;
}

const EduClawMedia = {
  showPlaceholder() {
    pauseVideo();
    show($('video-placeholder'));
    hide($('video-canvas'));
    hide($('video-player-host'));
  },

  showCanvas() {
    pauseVideo();
    hide($('video-placeholder'));
    hide($('video-player-host'));
    show($('video-canvas'));
  },

  async showPlayer({ src, poster, subtitlesUrl } = {}) {
    const video = getVideoEl();
    const player = getPlayerEl();
    if (!video || !player) return;

    hide($('video-placeholder'));
    hide($('video-canvas'));
    show($('video-player-host'));

    const videoSrc = src || DEMO_VIDEO;
    const posterSrc = poster ?? DEMO_POSTER;
    const captions = subtitlesUrl ?? subtitleUrlFromVideoUrl(videoSrc) ?? DEMO_SUBTITLES;

    video.pause();
    video.removeAttribute('src');
    video.load();

    setPoster(video, posterSrc);
    video.src = videoSrc;

    patchLearningRates(player);

    video.load();
    await attachCaptions(video, captions);

    try {
      await video.play();
    } catch {
      /* autoplay may be blocked until user gesture */
    }
  },

  reset() {
    pauseVideo();
    revokeCaptionBlob();
    const video = getVideoEl();
    if (video) {
      video.removeAttribute('src');
      video.load();
    }
    this.showPlaceholder();
  },

  demo: {
    video: DEMO_VIDEO,
    poster: DEMO_POSTER,
    subtitles: DEMO_SUBTITLES,
  },
};

window.EduClawMedia = EduClawMedia;

document.addEventListener('DOMContentLoaded', () => {
  const player = getPlayerEl();
  if (player) patchLearningRates(player);
});
