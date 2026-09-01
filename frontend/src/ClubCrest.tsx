import React, { useEffect, useMemo, useState } from 'react';

let spriteDataUri: string | null = null;
let spritePromise: Promise<string> | null = null;

function loadSprite() {
  if (spriteDataUri) return Promise.resolve(spriteDataUri);

  if (!spritePromise) {
    spritePromise = fetch('/club-logos-sprite.webp.b64?v=20260902', { cache: 'no-store' })
      .then((response) => {
        if (!response.ok) throw new Error(`Club crest sprite failed: ${response.status}`);
        return response.text();
      })
      .then((base64) => {
        const value = base64.trim();
        if (!value.startsWith('UklG')) {
          throw new Error('Club crest sprite response is not WebP base64');
        }
        spriteDataUri = `data:image/webp;base64,${value}`;
        return spriteDataUri;
      });
  }

  return spritePromise;
}

type ClubCrestProps = {
  crestUrl: string | null;
  name: string;
};

export default function ClubCrest({ crestUrl, name }: ClubCrestProps) {
  const [sprite, setSprite] = useState(spriteDataUri);
  const [failed, setFailed] = useState(false);

  const slot = useMemo(() => {
    const match = crestUrl?.match(/#slot=(\d+)$/);
    return match ? Number(match[1]) : null;
  }, [crestUrl]);

  useEffect(() => {
    if (slot === null || sprite || failed) return;

    loadSprite()
      .then(setSprite)
      .catch((error) => {
        console.error('Club crest sprite error', error);
        setFailed(true);
      });
  }, [slot, sprite, failed]);

  if (slot === null || failed) {
    return <span className="club-crest club-crest-missing" aria-label={`${name} crest unavailable`} />;
  }

  if (!sprite) {
    return <span className="club-crest club-crest-loading" aria-label={`${name} crest loading`} />;
  }

  const col = slot % 13;
  const row = Math.floor(slot / 13);

  return (
    <span
      className="club-crest"
      role="img"
      aria-label={`${name} crest`}
      style={{
        backgroundImage: `url("${sprite}")`,
        backgroundSize: '286px 286px',
        backgroundPosition: `${-col * 22}px ${-row * 22}px`,
      }}
    />
  );
}
