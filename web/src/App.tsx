import { useCallback, useEffect, useRef, useState } from "react";

type Asset = {
  id: string; filename: string; media_type: string; bytes: number;
  created_at: string; favorite: boolean; deleted_at: string | null;
};
type Album = { id: string; name: string; count: number };
type LibraryStats = {
  total: number; active: number; trashed: number; favorites: number;
  images: number; videos: number; original_bytes: number; albums: number;
};
const ENDPOINT = import.meta.env.VITE_PHOTOS_API_URL ?? "";
const PAGE_SIZE = 36;
const toDate = (value: string) => new Date(value).toLocaleDateString();
const labelSize = (value: number) => value < 1048576
  ? (value / 1024).toFixed(0) + " KB" : (value / 1048576).toFixed(1) + " MB";

async function api<T>(token: string, path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(ENDPOINT + path, {
    ...init,
    headers: { ...init.headers, Authorization: "Bearer " + token },
    cache: "no-store",
  });
  if (!response.ok) {
    let detail = "Request failed (" + response.status + ")";
    try {
      const data = await response.json();
      if (typeof data.detail === "string") detail = data.detail;
    } catch { /* non-JSON error */ }
    throw new Error(detail);
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>;
}

function Thumbnail({ token, asset }: { token: string; asset: Asset }) {
  const [src, setSrc] = useState<string>();
  useEffect(() => {
    if (asset.media_type.startsWith("video/")) return;
    let alive = true;
    let objectUrl: string | undefined;
    fetch(ENDPOINT + "/v1/assets/" + encodeURIComponent(asset.id) + "/thumbnail", {
      headers: { Authorization: "Bearer " + token }, cache: "no-store"
    }).then((res) => { if (!res.ok) throw Error("No thumbnail"); return res.blob(); })
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        if (alive) setSrc(objectUrl);
        else URL.revokeObjectURL(objectUrl);
      }).catch(() => { if (alive) setSrc(undefined); });
    return () => {
      alive = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [asset.id, asset.media_type, token]);
  return src ? <img className="thumbnail" src={src} alt="" loading="lazy"/> :
    <div className="placeholder" aria-hidden="true">{asset.media_type.startsWith("video/") ? "▶" : "▧"}</div>;
}

export default function App() {
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [assets, setAssets] = useState<Asset[]>([]);
  const [albums, setAlbums] = useState<Album[]>([]);
  const [stats, setStats] = useState<LibraryStats | null>(null);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const requestNumber = useRef(0);
  const [search, setSearch] = useState("");
  const [section, setSection] = useState<"library" | "favorites" | "trash">("library");
  const [albumId, setAlbumId] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [selected, setSelected] = useState<Asset | null>(null);
  const [preview, setPreview] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const dialog = useRef<HTMLElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);

  // A modal must receive keyboard focus, trap Tab, respond to Escape and restore
  // focus to the originating photo card when dismissed.
  useEffect(() => {
    if (!selected) return;
    closeButton.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setSelected(null);
      } else if (event.key === "Tab") {
        const nodes = Array.from(dialog.current?.querySelectorAll<HTMLElement>(
          'button:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])'
        ) ?? []);
        if (!nodes.length) return;
        const first = nodes[0]; const last = nodes[nodes.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault(); last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault(); first.focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      if (previousFocus.current?.isConnected) previousFocus.current.focus();
      previousFocus.current = null;
    };
  }, [selected]);

  const refresh = useCallback(async () => {
    if (!token) return;
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (section === "favorites") params.set("favorite", "true");
    if (section === "trash") params.set("trashed", "true");
    params.set("limit", String(PAGE_SIZE));
    params.set("offset", String(page * PAGE_SIZE));
    const activeRequest = ++requestNumber.current;
    try {
      const [assetData, albumData, statsData] = await Promise.all([
        api<{ items: Asset[]; total: number }>(token, albumId
          ? "/v1/albums/" + encodeURIComponent(albumId) + "/assets?" + params
          : "/v1/assets?" + params),
        api<{ items: Album[] }>(token, "/v1/albums"),
        api<LibraryStats>(token, "/v1/library/stats")
      ]);
      if (activeRequest !== requestNumber.current) return;
      if (page > 0 && page * PAGE_SIZE >= assetData.total) { setPage(page - 1); return; }
      setAssets(assetData.items);
      setTotal(assetData.total);
      setAlbums(albumData.items);
      setStats(statsData);
    } catch (e) {
      if (activeRequest === requestNumber.current) setNotice((e as Error).message);
    }
  }, [token, search, section, albumId, page]);

  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => {
    if (!selected || !token) return;
    let alive = true; let localUrl = "";
    fetch(ENDPOINT + "/v1/assets/" + encodeURIComponent(selected.id) + "/original", {
      headers: { Authorization: "Bearer " + token }, cache: "no-store"
    }).then((r) => {
      if (!r.ok) throw Error("Unable to load original");
      return r.blob();
    }).then((blob) => {
      localUrl = URL.createObjectURL(blob);
      if (alive) setPreview(localUrl);
      else URL.revokeObjectURL(localUrl);
    }).catch((e: Error) => { if (alive) setNotice(e.message); });
    return () => { alive = false; setPreview(""); if (localUrl) URL.revokeObjectURL(localUrl); };
  }, [selected, token]);

  async function signin(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setNotice("");
    try {
      const res = await fetch(ENDPOINT + "/v1/session", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }), cache: "no-store"
      });
      if (!res.ok) throw Error(res.status === 429 ? "Too many attempts. Try later." : "Incorrect password or server unavailable.");
      const body: { access_token: string } = await res.json();
      setToken(body.access_token); setPassword("");
    } catch (e) { setNotice((e as Error).message); }
    finally { setBusy(false); }
  }

  async function uploadFiles(files: FileList | null) {
    if (!files || !files.length) return;
    setBusy(true); setNotice("");
    let uploaded = 0;
    try {
      for (const file of Array.from(files)) {
        const body = new FormData();
        body.append("file", file);
        await api(token, "/v1/assets", { method: "POST", body });
        uploaded += 1;
      }
      setNotice(uploaded + " uploaded securely.");
      await refresh();
    } catch (e) { setNotice(uploaded + " uploaded. " + (e as Error).message); await refresh(); }
    finally { setBusy(false); if (input.current) input.current.value = ""; }
  }

  async function perform(asset: Asset, action: "favorite" | "delete" | "restore") {
    try {
      if (action === "favorite") await api(token, "/v1/assets/" + asset.id + "/favorite",
        { method: "PATCH", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ favorite: !asset.favorite }) });
      else if (action === "delete") await api(token, "/v1/assets/" + asset.id, { method: "DELETE" });
      else await api(token, "/v1/assets/" + asset.id + "/restore", { method: "POST" });
      setSelected(null); await refresh();
    } catch (e) { setNotice((e as Error).message); }
  }

  async function createAlbum() {
    const name = window.prompt("Album name");
    if (!name?.trim()) return;
    try {
      await api(token, "/v1/albums", { method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim() }) });
      await refresh();
    } catch (e) { setNotice((e as Error).message); }
  }

  async function addToAlbum(asset: Asset, id: string) {
    try {
      await api(token, "/v1/albums/" + id + "/assets/" + asset.id, { method: "POST" });
      setNotice("Added to album.");
      await refresh();
    } catch (e) { setNotice((e as Error).message); }
  }

  async function renameAlbum() {
    const album = albums.find(item => item.id === albumId);
    if (!album) return;
    const entered = window.prompt("New album name", album.name);
    if (!entered?.trim() || entered.trim() === album.name) return;
    try {
      await api(token, "/v1/albums/" + encodeURIComponent(albumId), {
        method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: entered.trim() })
      });
      setNotice("Album renamed.");
      await refresh();
    } catch (e) { setNotice((e as Error).message); }
  }

  async function deleteAlbum() {
    const album = albums.find(item => item.id === albumId);
    if (!album || !window.confirm('Delete album "' + album.name +
      '"? The photos will remain in your library.')) return;
    try {
      await api(token, "/v1/albums/" + encodeURIComponent(albumId), { method: "DELETE" });
      setPage(0); setAlbumId(""); setNotice("Album deleted. Your photos were kept.");
    } catch (e) { setNotice((e as Error).message); }
  }

  async function removeFromAlbum(asset: Asset) {
    if (!albumId) return;
    try {
      await api(token, "/v1/albums/" + encodeURIComponent(albumId) +
        "/assets/" + encodeURIComponent(asset.id), { method: "DELETE" });
      setNotice("Removed from album. Original photo is still in your library.");
      await refresh();
    } catch (e) { setNotice((e as Error).message); }
  }

  if (!token) return <main className="login-wrap">
    <section className="login-card">
      <div className="brand-mark" aria-hidden="true">✦</div>
      <p className="eyebrow">YOUR MOMENTS. YOUR CLOUD.</p>
      <h1>GoreeCloud Photos</h1>
      <p>Private photo and video storage, hosted under your control.</p>
      <form onSubmit={signin}>
        <label htmlFor="password">Library password</label>
        <input id="password" autoComplete="current-password" type="password" required
          value={password} onChange={(e) => setPassword(e.target.value)} />
        <button type="submit" className="primary" disabled={busy}>{busy ? "Unlocking…" : "Unlock library"}</button>
      </form>
      {notice && <p role="alert" className="message">{notice}</p>}
      <p className="footer-note">Use a trusted connection. Your password is not stored in this browser.</p>
    </section>
  </main>;

  return <div className="app-layout">
    <aside className="sidebar" aria-label="Library navigation">
      <div className="logo"><span aria-hidden="true">✦</span> GoreeCloud <strong>Photos</strong></div>
      <nav aria-label="Photo views">
        {(["library", "favorites", "trash"] as const).map((id) =>
          <button key={id} className={section === id && !albumId ? "active nav-item" : "nav-item"}
            onClick={() => { setPage(0); setAlbumId(""); setSection(id); }}>
            <span aria-hidden="true">{id === "library" ? "▦" : id === "favorites" ? "♡" : "⌫"}</span>
            {id === "library" ? "All photos" : id === "favorites" ? "Favorites" : "Trash"}
          </button>)}
      </nav>
      <div className="album-head"><strong>Albums</strong><button aria-label="Create album" onClick={createAlbum}>＋</button></div>
      <nav aria-label="Albums">{albums.map((album) =>
        <button key={album.id} className={albumId === album.id ? "active nav-item" : "nav-item"}
          onClick={() => { setPage(0); setAlbumId(album.id); setSection("library"); }}>
          <span aria-hidden="true">▧</span><span>{album.name}</span><small>{album.count}</small>
        </button>)}</nav>
      <p className="sidebar-foot">Self-hosted · No tracking</p>
    </aside>
    <main className="workspace">
      <header className="topbar">
        <div className="brand-mobile">✦ GoreeCloud Photos</div>
        <label className="search">
          <span aria-hidden="true">⌕</span><span className="visually-hidden">Search filenames</span>
          <input type="search" placeholder="Search your library" value={search}
            onChange={(e) => { setPage(0); setSearch(e.target.value); }} />
        </label>
        <button className="quiet" onClick={async () => {
          await api(token, "/v1/session", { method: "DELETE" }).catch(() => undefined);
          requestNumber.current += 1;
          setToken(""); setSelected(null); setAssets([]); setAlbums([]); setPage(0); setTotal(0);
          setStats(null);
        }}>Lock</button>
      </header>
      <div className="content">
        <div className="hero">
          <div>
            <p className="eyebrow">MEMORIES, IN YOUR HANDS</p>
            <h1>{albumId ? albums.find(a => a.id === albumId)?.name ?? "Album"
              : section === "favorites" ? "Favorites" : section === "trash" ? "Trash" : "Your moments"}</h1>
            <p className="subtitle">{section === "trash" ? "Hidden from your library. Restore any item." :
              "A home for the memories you choose to keep."}</p>
          </div>
          <div>
            <input ref={input} type="file" multiple accept="image/jpeg,image/png,image/webp,image/gif,video/mp4"
              className="visually-hidden" id="fileUpload" onChange={(e) => void uploadFiles(e.target.files)} />
            <button className="primary upload" disabled={busy} onClick={() => input.current?.click()}>
              {busy ? "Uploading…" : "＋ Add photos"}
            </button>
          </div>
        </div>
        {stats && <section className="library-metrics" aria-label="Private library statistics">
          <dl>
            <div><dt>Active items</dt><dd>{stats.active.toLocaleString()}</dd></div>
            <div><dt>Favorites</dt><dd>{stats.favorites.toLocaleString()}</dd></div>
            <div><dt>In trash</dt><dd>{stats.trashed.toLocaleString()}</dd></div>
            <div><dt>Stored originals</dt><dd>{labelSize(stats.original_bytes)}</dd></div>
          </dl>
          <p>Storage includes originals in trash. Nothing is shared or analyzed automatically.</p>
        </section>}
        {albumId && <div className="album-commands" role="group" aria-label="Album actions">
          <button type="button" onClick={() => void renameAlbum()}>Rename album</button>
          <button type="button" onClick={() => void deleteAlbum()}>Delete album</button>
          <small>Deleting an album never deletes its photos.</small>
        </div>}
        {notice && <p className="message" role="status">{notice}
          <button onClick={() => setNotice("")} aria-label="Dismiss message">×</button></p>}
        <div className="section-head"><h2>{assets.length ? "Your collection" : "Nothing here yet"}</h2>
          <span aria-live="polite">{total} total · {assets.length} shown</span></div>
        {assets.length ? <div className="photo-grid">
          {assets.map(asset => <article key={asset.id} className="photo-card">
            <button className="photo-open" disabled={section === "trash"}
              title={section === "trash" ? "Restore to preview" : "Open " + asset.filename}
              onClick={() => {
                previousFocus.current = document.activeElement as HTMLElement | null;
                setSelected(asset);
              }}>
              <Thumbnail token={token} asset={asset}/>
              <span className="card-title">{asset.filename}</span>
              <span className="card-date">{toDate(asset.created_at)} · {labelSize(asset.bytes)}</span>
            </button>
            <div className="card-actions">
              {section === "trash" ? <button onClick={() => void perform(asset, "restore")}>Restore</button> :
              <>
                <button aria-label={asset.favorite ? "Remove from favorites" : "Favorite"}
                  title={asset.favorite ? "Remove favorite" : "Favorite"}
                  onClick={() => void perform(asset, "favorite")}>{asset.favorite ? "♥" : "♡"}</button>
                {albumId && <button aria-label={"Remove " + asset.filename + " from this album"}
                  title="Remove from album (keep original)"
                  onClick={() => void removeFromAlbum(asset)}>Remove</button>}
                <button aria-label={"Move " + asset.filename + " to trash"}
                  title="Move to trash" onClick={() => void perform(asset, "delete")}>⌫</button>
                {!!albums.length && <select aria-label={"Add " + asset.filename + " to album"} value=""
                  onChange={(e) => { if (e.target.value) void addToAlbum(asset, e.target.value); }}>
                  <option value="">Add to album…</option>
                  {albums.map(a => <option value={a.id} key={a.id}>{a.name}</option>)}
                </select>}
              </>}
            </div>
          </article>)}
        </div> : <section className="empty">
          <div className="empty-symbol" aria-hidden="true">▧</div>
          <h3>Every memory begins somewhere.</h3>
          <p>Add photos or videos from your device to build your private collection.</p>
          <button className="primary" onClick={() => input.current?.click()}>Upload your first photo</button>
        </section>}
        {total > PAGE_SIZE && <nav className="pagination" aria-label="Photo pages">
          <button type="button" disabled={page === 0} onClick={() => setPage(p => Math.max(0, p - 1))}>
            Previous
          </button>
          <span aria-live="polite">Page {page + 1} of {Math.ceil(total / PAGE_SIZE)}</span>
          <button type="button" disabled={(page + 1) * PAGE_SIZE >= total} onClick={() => setPage(p => p + 1)}>
            Next
          </button>
        </nav>}
      </div>
    </main>
    {selected && <div className="modal-backdrop" role="presentation" onMouseDown={(e) => {
      if (e.target === e.currentTarget) setSelected(null);
    }}>
      <section ref={dialog} className="photo-dialog" role="dialog" aria-modal="true"
        aria-label={"Photo preview: " + selected.filename}>
        <div className="dialog-head"><strong>{selected.filename}</strong>
          <button ref={closeButton} aria-label="Close preview" onClick={() => setSelected(null)}>✕</button></div>
        <div className="dialog-body">{preview
          ? selected.media_type.startsWith("video/")
            ? <video controls src={preview} playsInline />
            : <img src={preview} alt={selected.filename}/>
          : <p>Loading original…</p>}</div>
        <div className="dialog-foot"><span>{toDate(selected.created_at)} · {labelSize(selected.bytes)}</span>
          {preview && <a className="primary download" href={preview} download={selected.filename}>Save original</a>}
        </div>
      </section>
    </div>}
  </div>;
}
