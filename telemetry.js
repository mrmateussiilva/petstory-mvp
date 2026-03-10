/**
 * PetStory Telemetry - Lightweight tracking script
 * Sends user behavior events to the backend
 */

(function() {
  'use strict';

  const TELEMETRY_ENDPOINT = '/telemetry/event';
  const SESSION_KEY = 'petstory_session_id';
  const SCROLL_KEY = 'petstory_scroll_depth';

  let sessionId = null;
  let scrollDepth = { 25: false, 50: false, 75: false, 100: false };
  let offerSeen = false;

  function generateSessionId() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  function getSessionId() {
    if (!sessionId) {
      sessionId = localStorage.getItem(SESSION_KEY);
      if (!sessionId) {
        sessionId = generateSessionId();
        localStorage.setItem(SESSION_KEY, sessionId);
      }
    }
    return sessionId;
  }

  function getBaseEventData(eventName) {
    return {
      session_id: getSessionId(),
      event_name: eventName,
      path: window.location.pathname || '/',
      timestamp: new Date().toISOString(),
      referrer: document.referrer || '',
      user_agent: navigator.userAgent || '',
      screen_width: window.screen.width,
      screen_height: window.screen.height
    };
  }

  function sendEvent(eventName, metadata) {
    const eventData = getBaseEventData(eventName);
    if (metadata) {
      eventData.metadata = metadata;
    }

    if (navigator.sendBeacon) {
      const blob = new Blob([JSON.stringify(eventData)], { type: 'application/json' });
      navigator.sendBeacon(TELEMETRY_ENDPOINT, blob);
    } else {
      fetch(TELEMETRY_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(eventData),
        keepalive: true
      }).catch(function() {});
    }
  }

  function handlePageView() {
    sendEvent('page_view');
  }

  function handleScroll() {
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrollPercent = docHeight > 0 ? Math.round((scrollTop / docHeight) * 100) : 0;

    const depthMap = { 25: 25, 50: 50, 75: 75, 100: 100 };

    for (const [key, threshold] of Object.entries(depthMap)) {
      if (scrollPercent >= threshold && !scrollDepth[key]) {
        scrollDepth[key] = true;
        sendEvent('scroll_' + threshold);
      }
    }
  }

  function handleOfferSeen() {
    if (!offerSeen) {
      const offerSection = document.getElementById('offer-section');
      if (offerSection) {
        const rect = offerSection.getBoundingClientRect();
        const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
        if (isVisible) {
          offerSeen = true;
          sendEvent('offer_seen');
        }
      }
    }
  }

  function handleCtaClick(event) {
    const target = event.target.closest('[data-track]');
    if (target) {
      const eventName = target.getAttribute('data-track');
      const metadata = {};
      
      if (eventName === 'faq_open') {
        const faqHeader = target.closest('.faq-header');
        if (faqHeader) {
          const question = faqHeader.textContent.replace(/\+$/, '').trim();
          metadata.question = question;
        }
      }
      
      sendEvent(eventName, metadata);
    }
  }

  function handleVisibilityChange() {
    if (document.visibilityState === 'hidden') {
      sendEvent('page_exit');
    }
  }

  function init() {
    handlePageView();

    let scrollTimeout;
    window.addEventListener('scroll', function() {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(function() {
        handleScroll();
        handleOfferSeen();
      }, 100);
    }, { passive: true });

    document.addEventListener('click', handleCtaClick, { passive: true });

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('pagehide', function() {
      sendEvent('page_exit');
    });

    setTimeout(handleOfferSeen, 1000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose sendEvent globally for other scripts
  window.sendEvent = sendEvent;
})();
