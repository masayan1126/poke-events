"use client";

import { useMemo, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import type { AreaData, Category, EventItem, LocationFilter, Plan, SiteData } from "../types";

const TAG_CONFIG: Record<string, { label: string; className: string }> = {
  csp: { label: "CSP", className: "tag-csp" },
  large: { label: "大型", className: "tag-large" },
  near: { label: "駅近", className: "tag-near" },
  long: { label: "長時間", className: "tag-long" },
  night: { label: "夜開催", className: "tag-night" },
  full: { label: "満席", className: "tag-full" },
  beginner: { label: "初心者", className: "tag-beginner" }
};

const CATEGORY_ICON: Record<string, string> = {
  gym_battle: "剣",
  open_league: "杯",
  friend_battle: "友",
  self_event: "催"
};

function defaultLocationFilters(): LocationFilter[] {
  return [{ id: "all", name: "全エリア", description: "", keywords: [] }];
}

function getLocationFilters(data: AreaData) {
  return data.locationFilters?.length ? data.locationFilters : defaultLocationFilters();
}

function getLocationFilter(data: AreaData, id: string) {
  return getLocationFilters(data).find((filter) => filter.id === id) || getLocationFilters(data)[0];
}

function matchesLocationFilter(data: AreaData, event: EventItem, filterId: string) {
  const filter = getLocationFilter(data, filterId);
  if (!filter || filter.id === "all") return true;
  const keywords = filter.keywords || [];
  const text = `${event.venue || ""} ${event.address || ""} ${event.name || ""}`;
  return keywords.some((keyword) => text.includes(keyword));
}

function countEventsForLocation(data: AreaData, filterId: string) {
  return data.categories.flatMap((category) => category.events).filter((event) => matchesLocationFilter(data, event, filterId));
}

function getVisiblePlans(data: AreaData, selectedLocationFilter: string) {
  if (selectedLocationFilter === "all") return data.plans || [];
  return data.focusPlans?.[selectedLocationFilter] || data.plans || [];
}

function formatMonthDay(date: string, day: string) {
  const parsed = new Date(date.replace(/\//g, "-"));
  if (Number.isNaN(parsed.getTime())) return `${date}（${day}）`;
  return `${parsed.getMonth() + 1}/${parsed.getDate()}（${day}）`;
}

function shortCategoryName(name: string) {
  return name.split("：").pop()?.split(" / ")[0] || name;
}

function stars(rating: number) {
  return "★".repeat(rating) + "☆".repeat(Math.max(0, 5 - rating));
}

export default function EventPlanner({ data }: { data: SiteData }) {
  const [selectedDateIndex, setSelectedDateIndex] = useState(data.dates.length ? 0 : -1);
  const selectedDate = selectedDateIndex >= 0 ? data.dates[selectedDateIndex] : null;
  const initialAreaId = selectedDate ? Object.keys(selectedDate.areaData)[0] || "" : "";
  const [selectedAreaId, setSelectedAreaId] = useState(initialAreaId);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedLocationFilter, setSelectedLocationFilter] = useState("all");

  const area = data.areas.find((item) => item.id === selectedAreaId);
  const selectedData = selectedDate?.areaData[selectedAreaId] || null;

  const selectedLocationEvents = useMemo(() => {
    if (!selectedData) return [];
    return countEventsForLocation(selectedData, selectedLocationFilter);
  }, [selectedData, selectedLocationFilter]);

  function selectDate(index: number) {
    const nextDate = data.dates[index];
    const nextAreaId = nextDate ? Object.keys(nextDate.areaData)[0] || "" : "";
    setSelectedDateIndex(index);
    setSelectedAreaId(nextAreaId);
    setSelectedCategory("all");
    setSelectedLocationFilter("all");
  }

  function selectArea(areaId: string) {
    setSelectedAreaId(areaId);
    setSelectedCategory("all");
    setSelectedLocationFilter("all");
  }

  return (
    <main className="app-shell">
      <Header region={data.meta.region} reportDate={data.meta.reportDate} />
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">Pokemon Card Events</p>
          <h1>ポケカイベント</h1>
          <p className="hero-meta">{data.meta.reportDate} 時点</p>
        </div>
        {selectedData && selectedDate && (
          <div className="summary-strip" aria-label="現在の選択">
            <span>{formatMonthDay(selectedDate.date, selectedDate.day)}</span>
            <span>{area?.name}</span>
            <strong>{selectedData.filteredCount}件</strong>
          </div>
        )}
      </section>

      <section className="selector-panel" aria-label="日付とエリア">
        <ChipRail label="日付">
          {data.dates.map((date, index) => {
            const count = Object.values(date.areaData).reduce((sum, item) => sum + item.filteredCount, 0);
            return (
              <button
                className={`choice-chip ${index === selectedDateIndex ? "active" : ""}`}
                key={`${date.date}-${date.day}`}
                onClick={() => selectDate(index)}
                type="button"
              >
                <span>{formatMonthDay(date.date, date.day)}</span>
                <b>{count}件</b>
              </button>
            );
          })}
        </ChipRail>
        <ChipRail label="エリア">
          {data.areas.map((item) => {
            const areaData = selectedDate?.areaData[item.id];
            return (
              <button
                className={`choice-chip ${item.id === selectedAreaId ? "active" : ""}`}
                disabled={!areaData}
                key={item.id}
                onClick={() => selectArea(item.id)}
                type="button"
              >
                <span>{item.name}</span>
                <b>{areaData?.filteredCount || 0}件</b>
              </button>
            );
          })}
        </ChipRail>
      </section>

      {selectedData ? (
        <>
          <PlanSection data={selectedData} areaName={area?.name || ""} selectedLocationFilter={selectedLocationFilter} />
          <FilterDock
            data={selectedData}
            selectedCategory={selectedCategory}
            selectedLocationFilter={selectedLocationFilter}
            selectedLocationEvents={selectedLocationEvents.length}
            onSelectCategory={setSelectedCategory}
            onSelectLocation={(id) => {
              setSelectedLocationFilter(id);
              setSelectedCategory("all");
            }}
          />
          <EventSections data={selectedData} selectedCategory={selectedCategory} selectedLocationFilter={selectedLocationFilter} fallbackUrl={data.meta.searchUrl} />
          <Notes notes={selectedData.notes} />
        </>
      ) : (
        <div className="empty-state">イベントデータがありません</div>
      )}

      <footer className="footer">
        <p>
          データ元:{" "}
          <a href={data.meta.searchUrl} target="_blank" rel="noreferrer">
            ポケモンカードゲーム プレイヤーズクラブ
          </a>
        </p>
        <a className="source-button" href={data.meta.searchUrl} target="_blank" rel="noreferrer">
          Players Clubで確認
        </a>
      </footer>
    </main>
  );
}

function Header({ region, reportDate }: { region: string; reportDate: string }) {
  return (
    <header className="top-bar">
      <div className="brand-mark">PK</div>
      <div>
        <div className="brand-title">ポケカイベント</div>
        <div className="brand-sub">{region}</div>
      </div>
      <div className="top-date">{reportDate}</div>
    </header>
  );
}

function ChipRail({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="chip-group">
      <div className="chip-label">{label}</div>
      <div className="chip-rail">{children}</div>
    </div>
  );
}

function PlanSection({ data, areaName, selectedLocationFilter }: { data: AreaData; areaName: string; selectedLocationFilter: string }) {
  const plans = getVisiblePlans(data, selectedLocationFilter);
  const filter = getLocationFilter(data, selectedLocationFilter);
  const subtitle = filter?.id !== "all" ? `${filter.name}の専用プラン` : `${areaName}のおすすめプラン`;

  return (
    <section className="plans-section" aria-label="行動プラン">
      <div className="section-heading">
        <div className="section-symbol">計</div>
        <div>
          <h2>行動プラン提案</h2>
          <p>{subtitle}</p>
        </div>
      </div>
      <div className="plans-grid">
        {plans.map((plan, index) => (
          <PlanCard index={index} key={plan.id} plan={plan} />
        ))}
      </div>
    </section>
  );
}

function PlanCard({ index, plan }: { index: number; plan: Plan }) {
  const [open, setOpen] = useState(true);

  return (
    <article className={`plan-card ${open ? "open" : ""}`}>
      <button className="plan-toggle" onClick={() => setOpen((value) => !value)} type="button">
        <span className="plan-badge">P{index + 1}</span>
        <span className="plan-main">
          <strong>{plan.name}</strong>
          <small>{plan.subtitle}</small>
        </span>
        <span className="rating">{stars(plan.rating)}</span>
        <span className="chevron" aria-label={open ? "閉じる" : "開く"}>
          {open ? "⌃" : "⌄"}
        </span>
      </button>
      {open && (
        <div className="plan-body">
          {plan.steps.map((step, index) => {
            const content = (
              <>
                <time>{step.time}</time>
                <span>
                  <strong>{step.event}</strong>
                  <small>{step.venue}</small>
                  <em>{step.area}</em>
                </span>
              </>
            );
            return step.url ? (
              <a className="plan-step" href={step.url} key={`${step.time}-${index}`} target="_blank" rel="noreferrer">
                {content}
              </a>
            ) : (
              <div className="plan-step" key={`${step.time}-${index}`}>
                {content}
              </div>
            );
          })}
          <p className="plan-merit">
            <b>メリット</b>
            {plan.merit}
          </p>
        </div>
      )}
    </article>
  );
}

function FilterDock({
  data,
  selectedCategory,
  selectedLocationFilter,
  selectedLocationEvents,
  onSelectCategory,
  onSelectLocation
}: {
  data: AreaData;
  selectedCategory: string;
  selectedLocationFilter: string;
  selectedLocationEvents: number;
  onSelectCategory: (id: string) => void;
  onSelectLocation: (id: string) => void;
}) {
  return (
    <nav className="filter-dock" aria-label="イベント絞り込み">
      <div className="filter-row">
        {getLocationFilters(data).map((filter) => (
          <button
            className={`filter-pill location ${filter.id === selectedLocationFilter ? "active" : ""}`}
            key={filter.id}
            onClick={() => onSelectLocation(filter.id)}
            title={filter.description || filter.name}
            type="button"
          >
            {filter.name}
            <b>{countEventsForLocation(data, filter.id).length}</b>
          </button>
        ))}
      </div>
      <div className="filter-row category-row">
        <button className={`filter-pill ${selectedCategory === "all" ? "active" : ""}`} onClick={() => onSelectCategory("all")} type="button">
          すべて
          <b>{selectedLocationEvents}</b>
        </button>
        {data.categories.map((category) => {
          const count = category.events.filter((event) => matchesLocationFilter(data, event, selectedLocationFilter)).length;
          return (
            <button
              className={`filter-pill ${selectedCategory === category.id ? "active" : ""}`}
              key={category.id}
              onClick={() => onSelectCategory(category.id)}
              style={{ "--accent": category.color } as CSSProperties}
              type="button"
            >
              <span className="filter-dot" />
              {shortCategoryName(category.name)}
              <b>{count}</b>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

function EventSections({
  data,
  selectedCategory,
  selectedLocationFilter,
  fallbackUrl
}: {
  data: AreaData;
  selectedCategory: string;
  selectedLocationFilter: string;
  fallbackUrl: string;
}) {
  const sections = data.categories
    .filter((category) => selectedCategory === "all" || selectedCategory === category.id)
    .map((category) => ({
      category,
      events: category.events.filter((event) => matchesLocationFilter(data, event, selectedLocationFilter))
    }))
    .filter((section) => section.events.length);

  if (!sections.length) return <div className="empty-state">該当するイベントがありません</div>;

  return (
    <section className="events-area" aria-label="イベント一覧">
      {sections.map(({ category, events }) => (
        <CategorySection category={category} events={events} fallbackUrl={fallbackUrl} key={category.id} />
      ))}
    </section>
  );
}

function CategorySection({ category, events, fallbackUrl }: { category: Category; events: EventItem[]; fallbackUrl: string }) {
  return (
    <section className="category-section">
      <div className="category-heading">
        <span className="category-icon" style={{ backgroundColor: category.color }}>
          {CATEGORY_ICON[category.id] || "札"}
        </span>
        <div>
          <h2>{category.name}</h2>
          <p>{events.length}件</p>
        </div>
      </div>
      <div className="event-grid">
        {events.map((event) => (
          <EventCard category={category} event={event} fallbackUrl={fallbackUrl} key={event.id} />
        ))}
      </div>
    </section>
  );
}

function EventCard({ category, event, fallbackUrl }: { category: Category; event: EventItem; fallbackUrl: string }) {
  return (
    <article className="event-card" style={{ "--accent": category.color } as CSSProperties}>
      <a href={event.url || fallbackUrl} target="_blank" rel="noreferrer">
        <div className="event-topline">
          <time>{event.time}</time>
          <span className="event-tags">
            {event.tags.map((tag) => {
              const config = TAG_CONFIG[tag];
              return config ? (
                <b className={`tag ${config.className}`} key={tag}>
                  {config.label}
                </b>
              ) : null;
            })}
          </span>
        </div>
        <h3>{event.name}</h3>
        <p className="venue">{event.venue}</p>
        <p className="address">{event.address}</p>
        <div className="event-meta">
          <span>{event.fee}</span>
          <span>{event.capacity}</span>
          <span>{event.distance}</span>
        </div>
      </a>
    </article>
  );
}

function Notes({ notes }: { notes: string[] }) {
  if (!notes.length) return null;

  return (
    <section className="notes-card">
      <h2>注意事項</h2>
      <ul>
        {notes.map((note) => (
          <li key={note}>{note}</li>
        ))}
      </ul>
    </section>
  );
}
