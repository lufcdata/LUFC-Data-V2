import React, { useMemo, useState } from 'react';
import spriteUrl from './assets/club-logos-sprite.webp';

type ClubCrestProps = {
  crestUrl: string | null;
  name: string;
};

export default function ClubCrest({ crestUrl, name }: ClubCrestProps) {
  const [imageFailed, setImageFailed] = useState(false);

  const slot = useMemo(() => {
    const match = crestUrl?.match(/#slot=(\d+)$/);
    return match ? Number(match[1]) : null;
  }, [crestUrl]);

  const directImageUrl = crestUrl && !crestUrl.includes('#slot=') ? crestUrl : null;

  if (directImageUrl && !imageFailed) {
    return (
      <img
        className="club-crest"
        src={directImageUrl}
        alt={`${name} crest`}
        loading="lazy"
        decoding="async"
        onError={() => setImageFailed(true)}
      />
    );
  }

  if (slot === null) {
    return <span className="club-crest club-crest-missing" aria-label={`${name} crest unavailable`} />;
  }

  const col = slot % 13;
  const row = Math.floor(slot / 13);

  return (
    <span
      className="club-crest"
      role="img"
      aria-label={`${name} crest`}
      style={{
        backgroundImage: `url(${spriteUrl})`,
        backgroundSize: '286px 286px',
        backgroundPosition: `${-col * 22}px ${-row * 22}px`,
      }}
    />
  );
}
