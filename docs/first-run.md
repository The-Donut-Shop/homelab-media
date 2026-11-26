# First run

Everything below is one-time setup after `docker compose up -d --build`.
Ports are the host ports from `compose.yaml`.

## 1. Folders

```bash
source .env
mkdir -p "$DATA"/downloads/{torrents/{movies,series,music,books,audiobooks,incomplete},soulseek/{complete,incomplete},cwa-ingest} \
         "$DATA"/media/{movies,series,music,books,audiobooks,podcasts,.recycle}
```

## 2. Downloads

- **qBittorrent** (`:8080`): Options → Downloads → *Default Torrent Management Mode: Automatic*,
  default save path `/data/downloads/torrents`, incomplete `/data/downloads/torrents/incomplete`.
  Categories (save paths under `/data/downloads/torrents/`): `movies`, `series`, `music`, `books`, `audiobooks`.
- **slskd** (`:5030`): in `${APPDATA}/slskd/slskd.yml` set your Soulseek login,
  `directories.downloads: /data/downloads/soulseek/complete`,
  `directories.incomplete: /data/downloads/soulseek/incomplete`,
  share `/data/media/music`, `soulseek.listen_port: 2234` (keep it out of the 32768-60999 ephemeral range),
  and an API key (`web.authentication.api_keys`) = `SLSKD_API_KEY` with **role `administrator`**
  (Aurral needs it to see slskd's download folder).

## 3. Indexers

**Prowlarr** (`:9696`): add indexers; Settings → Indexers → add a *FlareSolverr* proxy with host
`http://byparr:8191` (local, profile `cloudflare`) or `http://<other-machine>:8191` (see `remote/byparr/`)
and the tag `flaresolverr`; put that tag on Cloudflare-protected indexers (1337x, EZTV, Torrent Downloads).
Indexers used here: Knaben, The Pirate Bay, LimeTorrents, TorrentDownload, YTS,
MixtapeTorrent, and via Byparr 1337x, EZTV, Torrent Downloads. Internet Archive is added but
disabled: since 2026-11-25 archive.org stalls every request whose user agent says Prowlarr
(the same query from curl answers in ~1 s), so it only timed out. Re-enable it to check.

The host and the Byparr machine must not use the ISP's DNS resolver: it answers torrent sites
with a CNAME to the ISP's block page, which shows up in Prowlarr as
`Certificate validation for 1337x.to failed. RemoteCertificateNameMismatch`. See the
`homelab` repo, `host/resolved.conf.d/`, and `dns:` in `remote/byparr/compose.yaml`.
Settings → Apps: add Radarr (`http://radarr:7878`) and Sonarr (`http://sonarr:8989`) with
Prowlarr server `http://prowlarr:9696`.

## 4. Movies & series

**Radarr** / **Sonarr**:
- Root folder `/data/media/movies` / `/data/media/series`.
- Download client qBittorrent `qbittorrent:8080`, category `movies` / `series`.
- Media management: *Use Hardlinks instead of Copy* on, *Recycling Bin* `/data/media/.recycle/movies` /
  `/data/media/.recycle/series` (cleanup 14 days), import extra files `srt,ass,sub,idx`.
- Naming (Jellyfin-friendly):
  - Radarr folder `{Movie Title} ({Release Year}) [tmdbid-{TmdbId}]`, file `{Movie Title} ({Release Year}) [{Quality Full}]`
  - Sonarr folder `{Series Title} ({Series Year}) [tvdbid-{TvdbId}]`, season `Season {season:00}`,
    file `{Series Title} - S{season:00}E{episode:00} - {Episode Title} [{Quality Full}]`
- Radarr, small files first: Settings → Quality, *Preferred* size **15** MiB/min for the 720p qualities
  and **20** MiB/min for the 1080p ones (Remux untouched); that is ~1.7 GB / ~2.2 GB for a 111-minute film.
  Radarr still ranks by quality and seeders first; this only decides between copies of equal quality.
  The default (95, i.e. ~10 GB) made it take the biggest copy.
- Radarr, no Spanish dubs: Settings → Custom Formats → *Spanish dub*, one *Release Title* condition
  `(?i)[\[\(](esp|spa|cast)[\]\)]|\b(castellano|espa[ñn]ol)\b`, scored **−10000** in every quality profile
  (minimum score 0). Radarr reads `[Esp]` releases as English, so the profiles' language setting
  (*Original*) doesn't catch them.

To choose a release yourself: open the movie in Radarr → **Interactive Search**, sort by size and click the
download icon. Rejected releases (red icon; hover for the reason) can still be grabbed from there.

**Bazarr** (`:6767`): connect Sonarr and Radarr (API keys), language profile *English + Hindi*,
default profile for new series/movies, providers (Gestdown, YIFY, Embedded; plus SubDL, SubSource
and OpenSubtitles.com with free accounts), then *Wanted → Search All*.

**Seerr** (`:5055`): sign in with Jellyfin, add Radarr/Sonarr (`radarr`, `sonarr` hostnames).

**Cleanuparr** (`:11011`): connect qBittorrent, Radarr and Sonarr. Start with *Dry Run* on,
queue cleaner for stalled/failed downloads, never point the orphan scan at `/data/media`.

## 5. Music

**Aurral** (`:3001`): create the admin account, then Settings → Downloads:
slskd `http://slskd:5030` + `SLSKD_API_KEY`, Prowlarr `http://prowlarr:9696`,
qBittorrent `http://qbittorrent:8080` with category `music`. Keep yt-dlp last in the source order.

**Navidrome** (`:4533`) reads `/data/media/music` read-only; the `lyrics` container adds
`.lrc` files next to new tracks within ~2 minutes.

If a well-known song fails with *No suitable search results*, check the album shown on the
failed request. Aurral's song search sometimes picks a compilation copy, e.g. Zedd's
*Clarity* came from a promo DJ mix as a 3:20 edit, so every normal 4:31 copy failed the length
check. Request it from the artist's own album page instead. Versions that MusicBrainz doesn't
list (withdrawn or leaked ones) can't be requested in Aurral; search for them in slskd
(`:5030`) and move the file into `media/music/<Artist>/<Album>/` yourself.

## 6. Books

1. **Calibre-Web-Automated** (`:8183`): log in `admin` / `admin123`, **change the password**,
   enable uploads, Kobo sync (Admin → Basic Configuration → Feature Configuration) and set the
   external port/URL for the reverse proxy. Add SMTP for send-to-Kindle.
2. **Shelfmark** (`:8184`): uses Calibre-Web accounts (`AUTH_METHOD=cwa`); downloads land in
   `downloads/cwa-ingest`, which Calibre-Web-Automated imports and empties.
3. **Audiobookshelf** (`:13378`): create the root user, add a library at `/audiobooks`.

Reader apps: OPDS at `https://books.DOMAIN/opds`, KOReader sync at `https://books.DOMAIN/kosync`,
Kobo sync URL from Calibre-Web (user profile → *Kobo Sync Token*).

## 7. Dashboard

**Homepage** (`:3005`): fill the `*_API_KEY` values in `.env` (Bazarr: Settings → General;
Jellyfin: Dashboard → API Keys) and `docker compose up -d homepage`.
