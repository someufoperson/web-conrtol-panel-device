import React, { useEffect, useMemo, useState } from "react";

const API_URL = "http://localhost:8000/v1/devices"; // если vite proxy. Иначе: "http://localhost:8000/v1/devices"

function normalizeDevice(d) {
  return {
    id: d.device_id ?? d.device ?? "",
    status: (d.status ?? "").toString(),
    label: (d.label ?? "").toString(),
  };
}

function badgeClass(status) {
  const s = status.toLowerCase();
  if (s.includes("already")) return "badge badge-ok";
  if (s.includes("used")) return "badge badge-warn";
  return "badge badge-neutral";
}

export default function App() {
  const [devices, setDevices] = useState([]);
  const [draftLabels, setDraftLabels] = useState({}); // { [id]: string }
  const [saving, setSaving] = useState({}); // { [id]: boolean }
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [query, setQuery] = useState("");

  async function load() {
    setLoading(true);
    setErr("");
    try {
      const res = await fetch(API_URL, { headers: { Accept: "application/json" } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const list = Array.isArray(data?.devices) ? data.devices : [];
      const normalized = list.map(normalizeDevice).filter((x) => x.id);

      setDevices(normalized);

      // заполняем драфты (не перетирая уже редактируемые)
      setDraftLabels((prev) => {
        const next = { ...prev };
        for (const d of normalized) {
          if (next[d.id] === undefined) next[d.id] = d.label;
        }
        return next;
      });
    } catch (e) {
      setErr(e?.message ? String(e.message) : "Failed to load");
      setDevices([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return devices;
    return devices.filter((d) => {
      return (
        d.id.toLowerCase().includes(q) ||
        d.status.toLowerCase().includes(q) ||
        d.label.toLowerCase().includes(q)
      );
    });
  }, [devices, query]);

  async function saveLabel(deviceId) {
      const current = devices.find((d) => d.id === deviceId);
      if (!current) return;

      const newLabel = (draftLabels[deviceId] ?? "").trim();
      const oldLabel = current.label;

      if (newLabel === oldLabel) return;

  // показываем загрузку на строке
      setSaving((prev) => ({ ...prev, [deviceId]: true }));
      setErr("");

  // заглушка "сети": 650–950 мс
      const delay = 650 + Math.floor(Math.random() * 300);

      try {
    // имитация запроса
        await new Promise((resolve) => setTimeout(resolve, delay));

    // "успешное сохранение" — фиксируем в таблице
          setDevices((prev) =>
          prev.map((d) => (d.id === deviceId ? { ...d, label: newLabel } : d))
          );

    // на всякий: драфт приводим к сохранённому
          setDraftLabels((prev) => ({ ...prev, [deviceId]: newLabel }));
            } finally {
            setSaving((prev) => ({ ...prev, [deviceId]: false }));
            }
    }

  function onLabelKeyDown(e, deviceId) {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      saveLabel(deviceId);
    }
  }

  return (
    <div className="page">
      <div className="container">
        <header className="header">
          <div>
            <h1 className="title">Devices</h1>
            <p className="subtitle">Источник: {API_URL}</p>
          </div>

          <div className="headerActions">
            <button className="btn" onClick={load} disabled={loading}>
              {loading ? "Loading…" : "Refresh"}
            </button>
          </div>
        </header>

        <section className="panel">
          <div className="toolbar">
            <div className="searchWrap">
              <span className="searchIcon">⌕</span>
              <input
                className="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Поиск по id / статусу / имени…"
              />
            </div>

            <div className="meta">
              <span className="metaItem">Всего: {devices.length}</span>
              <span className="metaItem">Показано: {filtered.length}</span>
            </div>
          </div>

          {err && (
            <div className="alert">
              <div className="alertTitle">Сообщение</div>
              <div className="alertText">{err}</div>
              <div className="alertHint">
                Если это CORS — включи proxy в Vite или добавь CORS middleware в FastAPI.
                Если ошибка сохранения — проверь наличие эндпоинта PATCH /v1/devices/&lt;id&gt;.
              </div>
            </div>
          )}

          {!err && loading && (
            <div className="skeletonList">
              <div className="skeletonRow" />
              <div className="skeletonRow" />
              <div className="skeletonRow" />
            </div>
          )}

          {!loading && !err && (
            <>
              {filtered.length === 0 ? (
                <div className="empty">Ничего не найдено.</div>
              ) : (
                <div className="tableWrap">
                  <table className="table">
                    <thead>
                      <tr>
                        <th style={{ width: 220 }}>Device ID</th>
                        <th style={{ width: 170 }}>Status</th>
                        <th>Label (editable)</th>
                        <th style={{ width: 190 }}></th>
                      </tr>
                    </thead>

                    <tbody>
                      {filtered.map((d) => {
                        const draft = draftLabels[d.id] ?? d.label;
                        const isDirty = draft.trim() !== (d.label ?? "").trim();
                        const isSaving = !!saving[d.id];

                        return (
                          <tr key={d.id}>
                            <td>
                              <span className="mono">{d.id}</span>
                            </td>

                            <td>
                              <span className={badgeClass(d.status)}>
                                {d.status || "unknown"}
                              </span>
                            </td>

                            <td>
                              <input
                                className="cellInput"
                                value={draft}
                                onChange={(e) =>
                                  setDraftLabels((prev) => ({
                                    ...prev,
                                    [d.id]: e.target.value,
                                  }))
                                }
                                onKeyDown={(e) => onLabelKeyDown(e, d.id)}
                                placeholder="Введите label…"
                              />
                              <div className="cellHint">
                                Сохранение: кнопка Save или Ctrl+Enter
                              </div>
                            </td>

                            <td className="tdActions">
                                <div className="actions">
                                    <button
                                        className="btn btnSmall"
                                        onClick={() => navigator.clipboard.writeText(d.id)}
                                        title="Скопировать ID"
                                    >
                                    Copy ID
                                </button>

                                <button
                                    className="btn btnSmall btnPrimary"
                                    disabled={!isDirty || isSaving}
                                    onClick={() => saveLabel(d.id)}
                                    title="Сохранить label"
                                >
                                {isSaving ? "Saving…" : "Save"}
                                </button>
                                </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </section>

        <footer className="footer">
          <span>React UI • dark table</span>
        </footer>
      </div>
    </div>
  );
}