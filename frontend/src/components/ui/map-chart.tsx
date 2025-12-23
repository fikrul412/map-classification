import { Bar, BarChart, XAxis, YAxis, Tooltip, Legend } from "recharts";

interface MapChartProps {
  histogram: Record<string, number>;
}

export function MapChart({ histogram }: MapChartProps) {
  // convert object to array
  const chartData = Object.entries(histogram).map(([cls, count]) => ({
    class: cls,
    count: count as number,
  }));

  return (
    <BarChart width={400} height={200} data={chartData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
      <XAxis dataKey="class" />
      <YAxis />
      <Tooltip />
      <Legend />
      <Bar dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]} />
    </BarChart>
  );
}
