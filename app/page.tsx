import EventPlanner from "../src/components/EventPlanner";
import siteData from "../src/data/site-data.json";
import type { SiteData } from "../src/types";

export default function Page() {
  const data = siteData as SiteData;

  return (
    <>
      <script
        id="site-data"
        type="application/json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
      />
      <EventPlanner data={data} />
    </>
  );
}
