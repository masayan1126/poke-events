export type SiteData = {
  meta: {
    region: string;
    searchUrl: string;
    reportDate: string;
  };
  areas: Area[];
  dates: DateEntry[];
};

export type Area = {
  id: string;
  name: string;
};

export type DateEntry = {
  date: string;
  day: string;
  areaData: Record<string, AreaData>;
};

export type AreaData = {
  totalEvents: number;
  filteredCount: number;
  criteria?: string;
  categories: Category[];
  plans: Plan[];
  locationFilters?: LocationFilter[];
  focusPlans?: Record<string, Plan[]>;
  notes: string[];
};

export type Category = {
  id: string;
  name: string;
  color: string;
  events: EventItem[];
};

export type EventItem = {
  id: string | number;
  time: string;
  name: string;
  venue: string;
  address: string;
  fee: string;
  capacity: string;
  distance: string;
  url?: string;
  tags: string[];
};

export type Plan = {
  id: string | number;
  name: string;
  subtitle: string;
  rating: number;
  steps: PlanStep[];
  merit: string;
};

export type PlanStep = {
  time: string;
  event: string;
  venue: string;
  area: string;
  url?: string;
};

export type LocationFilter = {
  id: string;
  name: string;
  description?: string;
  keywords?: string[];
};
