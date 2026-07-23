import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  Check,
  Clock3,
  Download,
  Image as ImageIcon,
  KeyRound,
  Loader2,
  RefreshCw,
  Save,
  Sparkles,
} from "lucide-react";

import { API_URL } from "@/utils/apiClient";
import "./SocialFarmPage.css";

type Topic = {
  key: string;
  category: string;
  title: string;
};

type FarmSlide = {
  id: number;
  position: number;
  kind: "cover" | "body";
  heading: string;
  body: string[];
  scene_prompt: string;
  visual_type: string;
  image_provider: string;
  render_url: string;
  quality_warnings: string[];
};

type FarmPost = {
  id: number;
  slug: string;
  topic_key: string;
  category: string;
  title: string;
  caption: string;
  cta: string;
  status: string;
  copy_provider: string;
  quality_warnings: string[];
  created_at: string;
  updated_at: string;
  approved_at: string | null;
  slides: FarmSlide[];
};

const keyStorage = "televera:social-farm-api-key";

const SocialFarmPage = () => {
  const [apiKey, setApiKey] = useState(() => localStorage.getItem(keyStorage) ?? "");
  const [posts, setPosts] = useState<FarmPost[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [selectedPostId, setSelectedPostId] = useState<number | null>(null);
  const [selectedSlideId, setSelectedSlideId] = useState<number | null>(null);
  const [selectedTopic, setSelectedTopic] = useState("");
  const [forceLocalImages, setForceLocalImages] = useState(false);
  const [heading, setHeading] = useState("");
  const [bodyOne, setBodyOne] = useState("");
  const [bodyTwo, setBodyTwo] = useState("");
  const [loading, setLoading] = useState(false);
  const [action, setAction] = useState<string | null>(null);
  const [error, setError] = useState("");
  const initialLoadAttempted = useRef(false);

  const selectedPost = useMemo(
    () => posts.find((post) => post.id === selectedPostId) ?? posts[0] ?? null,
    [posts, selectedPostId],
  );
  const selectedSlide = useMemo(
    () =>
      selectedPost?.slides.find((slide) => slide.id === selectedSlideId) ??
      selectedPost?.slides[0] ??
      null,
    [selectedPost, selectedSlideId],
  );

  const apiFetch = useCallback(
    async (path: string, init?: RequestInit) => {
      const response = await fetch(`${API_URL}${path}`, {
        ...init,
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": apiKey,
          ...(init?.headers ?? {}),
        },
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail ?? `API-fel ${response.status}`);
      }
      return response;
    },
    [apiKey],
  );

  const replacePost = useCallback((updated: FarmPost) => {
    setPosts((current) => {
      const exists = current.some((post) => post.id === updated.id);
      if (!exists) return [updated, ...current];
      return current.map((post) => (post.id === updated.id ? updated : post));
    });
    setSelectedPostId(updated.id);
  }, []);

  const loadFarm = useCallback(async () => {
    if (!apiKey) return;
    setLoading(true);
    setError("");
    try {
      localStorage.setItem(keyStorage, apiKey);
      const [postsResponse, topicsResponse] = await Promise.all([
        apiFetch("/api/social-farm/posts"),
        apiFetch("/api/social-farm/topics"),
      ]);
      const postPayload = await postsResponse.json();
      const topicPayload = await topicsResponse.json();
      setPosts(postPayload.posts);
      setTopics(topicPayload);
      if (postPayload.posts.length) {
        setSelectedPostId((current) => current ?? postPayload.posts[0].id);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Kunde inte läsa farmen");
    } finally {
      setLoading(false);
    }
  }, [apiFetch, apiKey]);

  useEffect(() => {
    if (initialLoadAttempted.current) return;
    initialLoadAttempted.current = true;
    if (apiKey) void loadFarm();
  }, [apiKey, loadFarm]);

  useEffect(() => {
    if (!selectedSlide) return;
    setSelectedSlideId(selectedSlide.id);
    setHeading(selectedSlide.heading);
    setBodyOne(selectedSlide.body[0] ?? "");
    setBodyTwo(selectedSlide.body[1] ?? "");
  }, [selectedSlide]);

  const runAction = async (name: string, operation: () => Promise<void>) => {
    setAction(name);
    setError("");
    try {
      await operation();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Åtgärden misslyckades");
    } finally {
      setAction(null);
    }
  };

  const generate = () =>
    runAction("generate", async () => {
      const response = await apiFetch("/api/social-farm/generate", {
        method: "POST",
        body: JSON.stringify({
          topic_key: selectedTopic || null,
          force_local_images: forceLocalImages,
        }),
      });
      const generated = (await response.json()) as FarmPost;
      replacePost(generated);
      setSelectedSlideId(generated.slides[0]?.id ?? null);
    });

  const saveSlide = () => {
    if (!selectedPost || !selectedSlide) return Promise.resolve();
    return runAction("save", async () => {
      const response = await apiFetch(
        `/api/social-farm/posts/${selectedPost.id}/slides/${selectedSlide.id}`,
        {
          method: "POST",
          body: JSON.stringify({
            heading,
            body: selectedSlide.kind === "cover" ? [] : [bodyOne, bodyTwo],
          }),
        },
      );
      replacePost((await response.json()) as FarmPost);
    });
  };

  const regenerate = () => {
    if (!selectedPost || !selectedSlide) return Promise.resolve();
    return runAction("regenerate", async () => {
      const response = await apiFetch(
        `/api/social-farm/posts/${selectedPost.id}/slides/${selectedSlide.id}/regenerate`,
        {
          method: "POST",
          body: JSON.stringify({ force_local: forceLocalImages }),
        },
      );
      replacePost((await response.json()) as FarmPost);
    });
  };

  const approve = () => {
    if (!selectedPost) return Promise.resolve();
    return runAction("approve", async () => {
      const response = await apiFetch(`/api/social-farm/posts/${selectedPost.id}/approve`, {
        method: "POST",
      });
      replacePost((await response.json()) as FarmPost);
    });
  };

  const downloadZip = () => {
    if (!selectedPost) return Promise.resolve();
    return runAction("download", async () => {
      const response = await apiFetch(`/api/social-farm/posts/${selectedPost.id}/export`);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${selectedPost.slug}.zip`;
      anchor.click();
      URL.revokeObjectURL(url);
    });
  };

  const imageUrl = (slide: FarmSlide) =>
    `${API_URL}${slide.render_url}?v=${encodeURIComponent(selectedPost?.updated_at ?? "")}`;

  return (
    <main className="sf-page">
      <header className="sf-topbar">
        <div>
          <p className="sf-eyebrow">Televera internal</p>
          <h1>Social Farm</h1>
        </div>
        <div className="sf-key-control">
          <KeyRound size={16} aria-hidden />
          <input
            type="password"
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            placeholder="Intern API-nyckel"
            aria-label="Intern API-nyckel"
          />
          <button type="button" onClick={() => void loadFarm()} disabled={!apiKey || loading}>
            {loading ? <Loader2 className="sf-spin" size={16} /> : "Anslut"}
          </button>
        </div>
      </header>

      {error && (
        <div className="sf-error" role="alert">
          <AlertTriangle size={18} aria-hidden />
          {error}
        </div>
      )}

      <section className="sf-shell">
        <aside className="sf-sidebar">
          <div className="sf-create-card">
            <div className="sf-section-heading">
              <div>
                <p className="sf-eyebrow">Ny körning</p>
                <h2>Skapa sex slides</h2>
              </div>
              <Sparkles size={21} aria-hidden />
            </div>
            <label>
              Ämne
              <select value={selectedTopic} onChange={(event) => setSelectedTopic(event.target.value)}>
                <option value="">Automatisk rotation</option>
                {topics.map((topic) => (
                  <option value={topic.key} key={topic.key}>
                    {topic.title}
                  </option>
                ))}
              </select>
            </label>
            <label className="sf-checkbox">
              <input
                type="checkbox"
                checked={forceLocalImages}
                onChange={(event) => setForceLocalImages(event.target.checked)}
              />
              <span>
                <strong>Lokala bilder</strong>
                <small>Använd fallback och undvik API-kostnad.</small>
              </span>
            </label>
            <button
              className="sf-primary-button"
              type="button"
              onClick={() => void generate()}
              disabled={!apiKey || Boolean(action)}
            >
              {action === "generate" ? <Loader2 className="sf-spin" /> : <Sparkles />}
              Generera utkast
            </button>
          </div>

          <div className="sf-queue-heading">
            <h2>Utkast</h2>
            <span>{posts.length}</span>
          </div>
          <div className="sf-post-list">
            {posts.map((post) => (
              <button
                type="button"
                key={post.id}
                className={`sf-post-row ${selectedPost?.id === post.id ? "is-active" : ""}`}
                onClick={() => {
                  setSelectedPostId(post.id);
                  setSelectedSlideId(post.slides[0]?.id ?? null);
                }}
              >
                <span className={`sf-status-dot is-${post.status}`} />
                <span>
                  <strong>{post.title}</strong>
                  <small>
                    {new Intl.DateTimeFormat("sv-SE", {
                      day: "numeric",
                      month: "short",
                      hour: "2-digit",
                      minute: "2-digit",
                    }).format(new Date(post.created_at))}
                  </small>
                </span>
              </button>
            ))}
            {!loading && !posts.length && (
              <div className="sf-empty">
                <Clock3 size={24} />
                <p>Inga utkast ännu.</p>
              </div>
            )}
          </div>
        </aside>

        <section className="sf-workspace">
          {selectedPost ? (
            <>
              <div className="sf-workspace-header">
                <div>
                  <div className="sf-meta-row">
                    <span>{selectedPost.category}</span>
                    <span>{selectedPost.copy_provider} copy</span>
                    <span>{selectedPost.status === "approved" ? "godkänd" : "behöver granskas"}</span>
                  </div>
                  <h2>{selectedPost.title}</h2>
                </div>
                <div className="sf-header-actions">
                  <button type="button" onClick={() => void downloadZip()} disabled={Boolean(action)}>
                    {action === "download" ? <Loader2 className="sf-spin" /> : <Download />}
                    ZIP
                  </button>
                  <button
                    className="sf-approve-button"
                    type="button"
                    onClick={() => void approve()}
                    disabled={Boolean(action) || selectedPost.status === "approved"}
                  >
                    {action === "approve" ? <Loader2 className="sf-spin" /> : <Check />}
                    {selectedPost.status === "approved" ? "Godkänd" : "Godkänn"}
                  </button>
                </div>
              </div>

              {selectedPost.quality_warnings.length > 0 && (
                <div className="sf-warning-strip">
                  <AlertTriangle size={17} />
                  <span>{selectedPost.quality_warnings.length} QA-noteringar i utkastet</span>
                </div>
              )}

              <div className="sf-slide-grid">
                {selectedPost.slides.map((slide) => (
                  <button
                    type="button"
                    key={slide.id}
                    className={`sf-slide-card ${selectedSlide?.id === slide.id ? "is-active" : ""}`}
                    onClick={() => setSelectedSlideId(slide.id)}
                  >
                    <img src={imageUrl(slide)} alt={`Slide ${slide.position + 1}`} />
                    <span className="sf-slide-number">{slide.position + 1}</span>
                    <span className="sf-provider">{slide.image_provider}</span>
                    {slide.quality_warnings.length > 0 && (
                      <span className="sf-slide-warning">
                        <AlertTriangle size={13} />
                        {slide.quality_warnings.length}
                      </span>
                    )}
                  </button>
                ))}
              </div>

              {selectedSlide && (
                <div className="sf-editor">
                  <div className="sf-editor-preview">
                    <img src={imageUrl(selectedSlide)} alt="Vald slide i full storlek" />
                  </div>
                  <div className="sf-editor-fields">
                    <div className="sf-section-heading">
                      <div>
                        <p className="sf-eyebrow">Slide {selectedSlide.position + 1}</p>
                        <h3>Text och bakgrund</h3>
                      </div>
                      <ImageIcon size={20} />
                    </div>
                    <label>
                      Rubrik
                      <textarea rows={2} value={heading} onChange={(event) => setHeading(event.target.value)} />
                    </label>
                    {selectedSlide.kind !== "cover" && (
                      <>
                        <label>
                          Textblock 1
                          <textarea rows={3} value={bodyOne} onChange={(event) => setBodyOne(event.target.value)} />
                        </label>
                        <label>
                          Textblock 2
                          <textarea rows={3} value={bodyTwo} onChange={(event) => setBodyTwo(event.target.value)} />
                        </label>
                      </>
                    )}
                    <div className="sf-scene">
                      <span>Bildbrief</span>
                      <p>{selectedSlide.scene_prompt}</p>
                    </div>
                    {selectedSlide.quality_warnings.length > 0 && (
                      <ul className="sf-warning-list">
                        {selectedSlide.quality_warnings.map((warning) => (
                          <li key={warning}>{warning}</li>
                        ))}
                      </ul>
                    )}
                    <div className="sf-editor-actions">
                      <button type="button" onClick={() => void regenerate()} disabled={Boolean(action)}>
                        {action === "regenerate" ? <Loader2 className="sf-spin" /> : <RefreshCw />}
                        Ny bakgrund
                      </button>
                      <button
                        className="sf-primary-button"
                        type="button"
                        onClick={() => void saveSlide()}
                        disabled={Boolean(action)}
                      >
                        {action === "save" ? <Loader2 className="sf-spin" /> : <Save />}
                        Spara och rendera
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="sf-workspace-empty">
              <Sparkles size={36} />
              <h2>Skapa farmens första utkast</h2>
              <p>Välj ett ämne eller låt rotationen välja automatiskt.</p>
            </div>
          )}
        </section>
      </section>
    </main>
  );
};

export default SocialFarmPage;
