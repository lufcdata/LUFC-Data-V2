import React, { useEffect, useMemo, useState } from 'react';

let spriteObjectUrl: string | null = null;
let spritePromise: Promise<string> | null = null;

function loadSprite() {
  if (spriteObjectUrl) return Promise.resolve(spriteObjectUrl);
  if (!spritePromise) {
    spritePromise = fetch('/club-logos-sprite.b64')
      .then((response) => {
        if (!response.ok) throw new Error(`Club crest sprite failed: ${response.status}`);
        return response.text();
      })
      .then((base64) => {
        const binary = atob(base64.trim());
        const bytes = new Uint8Array(binary.length);
        for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
        spriteObjectUrl = URL.createObjectURL(new Blob([bytes], { type: 'image/png' }));
        return spriteObjectUrl;
      });
  }
  return spritePromise;
}

type ClubCrestProps = {
  crestUrl: string | null;
  name: string;
};

export default function ClubCrest({ crestUrl, name }: ClubCrestProps) {
  const [sprite, setSprite] = useState(spriteObjectUrl);
  const slot = useMemo(() => {
    const match = crestUrl?.match(/#slot=(\d+)$/);
    return match ? Number(match[1]) : null;
  }, [crestUrl]);

  useEffect(() => {
    if (slot === null || sprite) return;
    loadSprite().then(setSprite).catch((error) => console.error(error));
  }, [slot, sprite]);

  if (slot === null || !sprite) {
    return <span className="club-crest club-crest-loading" aria-label={`${name} crest`} />;
  }

  const col = slot % 13;
  const row = Math.floor(slot / 13);

  return (
    <span
      className="club-crest"
      role="img"
      aria-label={`${name} crest`}
      style={{
        backgroundImage: `url(${sprite})`,
        backgroundPosition: `${-col * 22}px ${-row * 22}px`,
      }}
    />
  );
}
