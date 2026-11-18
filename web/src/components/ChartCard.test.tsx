import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChartCard, StatTile } from "./ChartCard";

describe("ChartCard", () => {
  it("renders its title, optional subtitle, and children", () => {
    render(
      <ChartCard title="Monthly bookings" subtitle="Closed-Won revenue by month">
        <div>chart body</div>
      </ChartCard>,
    );
    expect(screen.getByText("Monthly bookings")).toBeInTheDocument();
    expect(screen.getByText("Closed-Won revenue by month")).toBeInTheDocument();
    expect(screen.getByText("chart body")).toBeInTheDocument();
  });

  it("omits the subtitle element entirely when none is given", () => {
    render(
      <ChartCard title="No subtitle">
        <div>body</div>
      </ChartCard>,
    );
    expect(screen.queryByText("Closed-Won revenue by month")).not.toBeInTheDocument();
  });
});

describe("StatTile", () => {
  it("renders label, value, and caption", () => {
    render(<StatTile label="Win rate" value="22.9%" caption="628 won / 2,116 lost" />);
    expect(screen.getByText("Win rate")).toBeInTheDocument();
    expect(screen.getByText("22.9%")).toBeInTheDocument();
    expect(screen.getByText("628 won / 2,116 lost")).toBeInTheDocument();
  });
});
