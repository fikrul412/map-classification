import { useState } from "react";
import { Card, CardTitle } from "./components/ui/card";
import { DatePicker } from "./components/ui/date-input";
import { MapImage } from "./components/ui/map-image";
import { MapPin, SquareArrowOutUpRightIcon } from "lucide-react";
import { InputGroup, InputGroupInput } from "./components/ui/input-group";
import { Button } from "./components/ui/button";
import { MenuEdit } from "./components/ui/menu-edit";
import { MapChart } from "./components/ui/map-chart";
import { Modal } from "./components/ui/modal";

type MapData = {
  year: number;
  histogram: Record<string, number>;
  img: string;
};

export default function App() {
  // --- STATES ---
  const [mapDataArr, setMapDataArr] = useState<MapData[]>([]);
  const [yearFrom, setYearFrom] = useState<number>(2021);
  const [yearTo, setYearTo] = useState<number>(2021);
  const [selectedYear, setSelectedYear] = useState<number>(2021);

  const [bbox, setBbox] = useState<number[]>([
    122.546729, -5.692516, 122.743073, -5.483401
  ]);

  const [clientId, setClientId] = useState("");
  const [clientPassword, setClientPassword] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("");

  const handleSaveClient = (id: string, password: string) => {
    setClientId(id);
    setClientPassword(password);
    setIsModalOpen(false);
  };

  // --- FETCH DATA ---
  const sendData = async () => {
    setLoading(true);
    setMapDataArr([]);

    const arr: MapData[] = [];

    for (let year = yearFrom; year <= yearTo; year++) {
      try {
        setLoadingText(`Processing year ${year}...`);

        const response = await fetch("http://localhost:5000/map", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            year,
            bbox,
            client_id: clientId,
            client_password: clientPassword,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error ${response.status}`);
        }

        const data = await response.json();

        arr.push({
          year,
          histogram: data.histogram,
          img: data.image_base64,
        });

      } catch (err) {
        console.error(err);
        alert(`Error processing year ${year}`);
        break;
      }
    }

    setMapDataArr(arr);
    if (arr.length > 0) setSelectedYear(arr[0].year);

    setLoading(false);
    setLoadingText("");
  };

  // --- DATA SESUAI TAHUN DIPILIH (UNTUK TAMPILAN) ---
  const selectedYearData = mapDataArr.find(d => d.year === selectedYear);

  return (
    <>
      {/* LOADING OVERLAY */}
      {loading && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-white px-6 py-4 rounded-lg text-center">
            <div className="animate-spin w-8 h-8 border-4 border-gray-300 border-t-gray-700 rounded-full mx-auto mb-3" />
            <p>{loadingText}</p>
          </div>
        </div>
      )}

      <div className="flex h-screen py-3">
        {/* ===== LEFT PANEL ===== */}
        <div className="w-1/2 flex flex-col items-center mx-3">
          <Card className="w-fit px-4 py-4 flex justify-between items-center">
            <CardTitle>Map Classification</CardTitle>
          </Card>

          <Card className="h-full w-full my-3 px-3 flex flex-col justify-between">
            <div className="w-full">
              <CardTitle className="mb-4">Coordinates:</CardTitle>
              <InputGroup className="px-2">
                <MapPin />
                <InputGroupInput
                  value={bbox.join(",")}
                  onChange={(e) => {
                    const vals = e.target.value.split(",").map(Number);
                    if (vals.length === 4) setBbox(vals);
                  }}
                />
                <a href="http://bboxfinder.com/" target="_blank">
                  <SquareArrowOutUpRightIcon />
                </a>
              </InputGroup>
            </div>

            <MapChart histogram={selectedYearData?.histogram || {}} />

            <div className="flex w-full justify-center gap-4 mt-4">
              <Button onClick={() => setIsModalOpen(true)}>
                Set Client ID
              </Button>
              <DatePicker
                value={selectedYear}
                onChange={(y) => setSelectedYear(Number(y))}
              />
              <MenuEdit />
            </div>
          </Card>
        </div>

        {/* ===== RIGHT PANEL ===== */}
        <div className="w-1/2 flex flex-col items-center mx-3">
          <Card className="h-full w-full mb-3 flex flex-col items-center px-5">
            <MapImage src={selectedYearData?.img || ""} />

            <div className="flex justify-around w-full mt-4">
              <CardTitle><span className="mx-3">From:</span></CardTitle>
              <DatePicker value={yearFrom} onChange={(y) => setYearFrom(Number(y))} />

              <CardTitle><span className="mx-3">To:</span></CardTitle>
              <DatePicker value={yearTo} onChange={(y) => setYearTo(Number(y))} />

              <Button onClick={sendData} disabled={loading}>
                Start
              </Button>
            </div>
          </Card>
        </div>
      </div>

      {/* MODAL */}
      {isModalOpen && (
        <Modal
          onClose={() => setIsModalOpen(false)}
          onSave={handleSaveClient}
        />
      )}
    </>
  );
}
