const POWER_BI_BASE_URL =
    "https://app.powerbi.com/reportEmbed?reportId=3c2edaec-6fda-4c9c-8f1a-bd50ec405e6f&autoAuth=true&ctid=1490b17d-5dc9-4cbf-aeba-a2e854f521b8";
const EXCEL_FILE = "EXCEL BMW sales data (2010-2024).xlsx";

const filterConfig = [
    { key: "Model_Name", elementId: "filter-model" },
    { key: "Manufacturing_Year", elementId: "filter-year" },
    { key: "Region", elementId: "filter-region" },
    { key: "Fuel_Type", elementId: "filter-fuel" },
    { key: "Transmission", elementId: "filter-transmission" },
    { key: "Vehicle_Type", elementId: "filter-vehicle" },
];

const regionColors = {
    Europe: "#63b3ff",
    Asia: "#5ae4a8",
    "South America": "#f97316",
    "North America": "#0ea5e9",
    Africa: "#94a3b8",
    "Middle East": "#ff4d57",
};

const appState = {
    rawData: [],
    filteredData: [],
    activePage: {
        label: "Executive Overview",
        id: "ReportSection",
    },
    spotlightModel: null,
};

document.addEventListener("DOMContentLoaded", () => {
    bindPageButtons();
    bindFilterEvents();
    bindResetButton();
    revealSections();
    loadExcelData();
});

async function loadExcelData() {
    setFooterStatus("Loading BMW sales workbook into the browser...");

    try {
        const response = await fetch(encodeURI(EXCEL_FILE));
        if (!response.ok) {
            throw new Error(`Unable to fetch workbook (${response.status})`);
        }

        const arrayBuffer = await response.arrayBuffer();
        const workbook = XLSX.read(arrayBuffer, { type: "array" });
        const firstSheet = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[firstSheet];
        const rows = XLSX.utils.sheet_to_json(worksheet, { raw: false, defval: "" });

        appState.rawData = rows.map(normalizeRow);
        populateFilters(appState.rawData);
        applyFiltersAndRefresh();

        setFooterStatus("BMW sales workbook loaded. Filters and premium analytics are now live.");
    } catch (error) {
        console.error(error);
        setFooterStatus("Workbook load failed. Run this folder through a local web server so the browser can fetch the Excel file.");
    }
}

function normalizeRow(row) {
    return {
        Model_Name: safeText(row.Model_Name),
        Manufacturing_Year: Number(cleanNumeric(row.Manufacturing_Year)),
        Region: safeText(row.Region),
        Color: safeText(row.Color),
        Fuel_Type: safeText(row.Fuel_Type),
        Transmission: safeText(row.Transmission),
        Engine_Size_L: cleanNumeric(row.Engine_Size_L),
        Odometer_Reading_KM: cleanNumeric(row.Odometer_Reading_KM),
        Price_USD: cleanNumeric(row.Price_USD),
        Sales_Volume: cleanNumeric(row.Sales_Volume),
        Sales_Classification: safeText(row.Sales_Classification),
        Revenue: cleanNumeric(row.Revenue),
        Vehicle_Type: safeText(row.Vehicle_Type),
        Claimed_Mileage: cleanNumeric(row["Claimed_Mileage_KM/L"]),
        Development_Nation: safeText(row.Development_Nation),
    };
}

function safeText(value) {
    return String(value ?? "").trim() || "Unknown";
}

function cleanNumeric(value) {
    if (value === null || value === undefined || value === "") {
        return 0;
    }
    const numeric = String(value).replace(/[^0-9.-]/g, "");
    return Number(numeric || 0);
}

function populateFilters(data) {
    filterConfig.forEach(({ key, elementId }) => {
        const element = document.getElementById(elementId);
        const values = [...new Set(data.map((item) => item[key]).filter(Boolean))].sort((a, b) => {
            if (typeof a === "number" && typeof b === "number") {
                return a - b;
            }
            return String(a).localeCompare(String(b));
        });

        element.innerHTML = values
            .map((value) => `<option value="${escapeHtml(String(value))}">${escapeHtml(String(value))}</option>`)
            .join("");
    });
}

function bindFilterEvents() {
    filterConfig.forEach(({ elementId }) => {
        document.getElementById(elementId).addEventListener("change", () => {
            applyFiltersAndRefresh();
        });
    });

    document.getElementById("spotlight-model").addEventListener("change", (event) => {
        appState.spotlightModel = event.target.value;
        renderModelSpotlight(appState.filteredData);
    });
}

function bindResetButton() {
    document.getElementById("reset-filters").addEventListener("click", () => {
        filterConfig.forEach(({ elementId }) => {
            const select = document.getElementById(elementId);
            [...select.options].forEach((option) => {
                option.selected = false;
            });
        });
        appState.spotlightModel = null;
        applyFiltersAndRefresh();
    });
}

function getSelectedValues(elementId) {
    return [...document.getElementById(elementId).selectedOptions].map((option) => option.value);
}

function applyFiltersAndRefresh() {
    if (!appState.rawData.length) {
        return;
    }

    const selectedFilters = Object.fromEntries(
        filterConfig.map(({ key, elementId }) => [key, getSelectedValues(elementId)])
    );

    appState.filteredData = appState.rawData.filter((row) =>
        Object.entries(selectedFilters).every(([key, selectedValues]) => {
            if (!selectedValues.length) {
                return true;
            }
            return selectedValues.includes(String(row[key]));
        })
    );

    updateMetaStrip(appState.filteredData);
    updateKpis(appState.filteredData);
    updateSpotlightOptions(appState.filteredData);

    if (!appState.filteredData.length) {
        renderEmptyCharts();
        setFooterStatus("No rows match the current filter combination. Adjust the sidebar selections to restore the dashboard view.");
        return;
    }

    renderModelSpotlight(appState.filteredData);
    renderRegionalDemand(appState.filteredData);
    renderProductMix(appState.filteredData);
    setFooterStatus(`Showing ${appState.filteredData.length.toLocaleString()} BMW sales rows with live analytics.`);
}

function updateMetaStrip(data) {
    document.getElementById("meta-records").textContent = `${data.length.toLocaleString()} records`;
    document.getElementById("meta-models").textContent = `${new Set(data.map((item) => item.Model_Name)).size} models`;
    document.getElementById("meta-regions").textContent = `${new Set(data.map((item) => item.Region)).size} regions`;
}

function updateKpis(data) {
    const totalRevenue = sum(data.map((item) => item.Revenue));
    const totalSales = sum(data.map((item) => item.Sales_Volume));
    const averagePrice = average(data.map((item) => item.Price_USD));
    const topModel = findTopKey(data, "Model_Name", "Revenue");
    const topRegion = findTopKey(data, "Region", "Revenue");

    document.getElementById("kpi-revenue").textContent = formatCurrency(totalRevenue);
    document.getElementById("kpi-sales").textContent = formatCompact(totalSales);
    document.getElementById("kpi-price").textContent = formatCurrency(averagePrice);
    document.getElementById("kpi-model").textContent = topModel || "--";
    document.getElementById("kpi-region").textContent = topRegion || "--";
}

function updateSpotlightOptions(data) {
    const modelSelect = document.getElementById("spotlight-model");
    const models = [...new Set(data.map((item) => item.Model_Name))].sort((a, b) => a.localeCompare(b));
    const fallbackModel = findTopKey(data, "Model_Name", "Revenue") || models[0] || "";

    if (!models.includes(appState.spotlightModel)) {
        appState.spotlightModel = fallbackModel;
    }

    modelSelect.innerHTML = models
        .map(
            (model) =>
                `<option value="${escapeHtml(model)}" ${
                    model === appState.spotlightModel ? "selected" : ""
                }>${escapeHtml(model)}</option>`
        )
        .join("");
}

function renderModelSpotlight(data) {
    if (!data.length) {
        return;
    }

    const spotlightModel = appState.spotlightModel || findTopKey(data, "Model_Name", "Revenue");
    const spotlightRows = data.filter((item) => item.Model_Name === spotlightModel);

    if (!spotlightRows.length) {
        return;
    }

    const modelSummary = summarizeModel(spotlightRows);
    const modelBenchmark = summarizeByKey(data, "Model_Name");
    const benchmarkValues = Object.values(modelBenchmark);

    setText("spotlight-price", formatCurrency(modelSummary.averagePrice));
    setText("spotlight-sales", formatCompact(modelSummary.totalSales));
    setText("spotlight-revenue", formatCurrency(modelSummary.totalRevenue));
    setText("spotlight-mileage", `${modelSummary.mileage.toFixed(1)} KM/L`);
    setText("spotlight-engine", `${modelSummary.engine.toFixed(1)} L`);
    setText("spotlight-fuel", modelSummary.fuelType);
    setText("spotlight-transmission", modelSummary.transmission);
    setText("spotlight-vehicle", modelSummary.vehicleType);

    const radarValues = [
        normalizeAgainst(modelSummary.totalSales, Math.max(...benchmarkValues.map((item) => item.totalSales))),
        normalizeAgainst(modelSummary.totalRevenue, Math.max(...benchmarkValues.map((item) => item.totalRevenue))),
        normalizeAgainst(modelSummary.averagePrice, Math.max(...benchmarkValues.map((item) => item.averagePrice))),
        normalizeAgainst(modelSummary.mileage, Math.max(...benchmarkValues.map((item) => item.mileage))),
        normalizeAgainst(modelSummary.engine, Math.max(...benchmarkValues.map((item) => item.engine))),
    ];

    Plotly.newPlot(
        "model-radar-chart",
        [
            {
                type: "scatterpolar",
                r: [...radarValues, radarValues[0]],
                theta: [
                    "Sales Strength",
                    "Revenue Strength",
                    "Price Level",
                    "Mileage Efficiency",
                    "Engine Performance",
                    "Sales Strength",
                ],
                fill: "toself",
                mode: "lines+markers",
                line: { color: "#34a6ff", width: 3 },
                marker: { color: "#ff4d57", size: 8 },
                fillcolor: "rgba(52, 166, 255, 0.20)",
                hovertemplate: "%{theta}: %{r:.1f}<extra></extra>",
            },
        ],
        {
            margin: { l: 28, r: 28, t: 18, b: 18 },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            showlegend: false,
            font: { color: "#dbe4ef", family: "Manrope" },
            polar: {
                bgcolor: "rgba(0,0,0,0)",
                radialaxis: {
                    visible: true,
                    range: [0, 100],
                    gridcolor: "rgba(130,160,200,0.18)",
                    linecolor: "rgba(130,160,200,0.18)",
                    tickfont: { color: "#8ea4bd" },
                },
                angularaxis: {
                    gridcolor: "rgba(130,160,200,0.10)",
                    linecolor: "rgba(130,160,200,0.10)",
                    tickfont: { color: "#edf3fa", size: 11 },
                },
            },
        },
        { displayModeBar: false, responsive: true }
    );
}

function renderRegionalDemand(data) {
    const grouped = groupByMany(data, ["Manufacturing_Year", "Region"]);
    const bubbleRows = Object.values(grouped).map((bucket) => ({
        year: bucket[0].Manufacturing_Year,
        region: bucket[0].Region,
        avgPrice: average(bucket.map((row) => row.Price_USD)),
        salesVolume: sum(bucket.map((row) => row.Sales_Volume)),
        revenue: sum(bucket.map((row) => row.Revenue)),
        developmentNation: mode(bucket.map((row) => row.Development_Nation)),
    }));

    const topSalesRegion = findTopKey(data, "Region", "Sales_Volume");
    const topRevenueRegion = findTopKey(data, "Region", "Revenue");
    const topPriceRegion = findTopAverageKey(data, "Region", "Price_USD");

    setText("region-top-sales", topSalesRegion || "--");
    setText("region-top-revenue", topRevenueRegion || "--");
    setText("region-top-price", topPriceRegion || "--");

    const years = [...new Set(bubbleRows.map((item) => item.year))].sort((a, b) => a - b);
    const firstYear = years[0];
    const initialRows = bubbleRows.filter((item) => item.year === firstYear);

    const traces = buildRegionalBubbleTraces(initialRows);
    const frames = years.map((year) => ({
        name: String(year),
        data: buildRegionalBubbleTraces(bubbleRows.filter((item) => item.year === year)),
    }));

    Plotly.newPlot(
        "regional-bubble-chart",
        traces,
        {
            margin: { l: 12, r: 12, t: 24, b: 32 },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            font: { color: "#dbe4ef", family: "Manrope" },
            showlegend: true,
            legend: {
                orientation: "h",
                y: 1.12,
                x: 0,
                bgcolor: "rgba(0,0,0,0)",
            },
            xaxis: {
                title: "Average Price (USD)",
                gridcolor: "rgba(130,160,200,0.14)",
                zeroline: false,
            },
            yaxis: {
                title: "Sales Volume",
                gridcolor: "rgba(130,160,200,0.14)",
                zeroline: false,
            },
            updatemenus: [
                {
                    type: "buttons",
                    direction: "left",
                    x: 0,
                    y: 1.18,
                    bgcolor: "rgba(0,0,0,0)",
                    buttons: [
                        {
                            label: "Play",
                            method: "animate",
                            args: [null, { fromcurrent: true, frame: { duration: 700, redraw: true }, transition: { duration: 350 } }],
                        },
                    ],
                },
            ],
            sliders: [
                {
                    active: 0,
                    currentvalue: {
                        prefix: "Year: ",
                        font: { color: "#edf3fa" },
                    },
                    steps: years.map((year) => ({
                        label: String(year),
                        method: "animate",
                        args: [[String(year)], { mode: "immediate", frame: { duration: 0, redraw: true }, transition: { duration: 250 } }],
                    })),
                },
            ],
        },
        { displayModeBar: false, responsive: true }
    ).then(() => {
        Plotly.addFrames("regional-bubble-chart", frames);
    });
}

function buildRegionalBubbleTraces(rows) {
    const groupedByRegion = groupBy(rows, "region");
    return Object.entries(groupedByRegion).map(([region, regionRows]) => ({
        type: "scatter",
        mode: "markers",
        name: region,
        x: regionRows.map((item) => item.avgPrice),
        y: regionRows.map((item) => item.salesVolume),
        text: regionRows.map(
            (item) =>
                `${item.region}<br>Revenue: ${formatCurrency(item.revenue)}<br>Development: ${item.developmentNation}`
        ),
        hovertemplate: "%{text}<br>Avg Price: %{x:$,.0f}<br>Sales Volume: %{y:,.0f}<extra></extra>",
        marker: {
            size: regionRows.map((item) => scaleBubble(item.revenue)),
            color: regionColors[region] || "#34a6ff",
            opacity: 0.82,
            line: { width: 1.2, color: "rgba(255,255,255,0.22)" },
        },
    }));
}

function renderProductMix(data) {
    const bestVehicle = findTopKey(data, "Vehicle_Type", "Sales_Volume");
    const bestTransmission = findTopKey(data, "Transmission", "Sales_Volume");
    const bestFuel = findTopKey(data, "Fuel_Type", "Sales_Volume");
    const strongestMix = findTopCombination(data, ["Vehicle_Type", "Fuel_Type", "Transmission"], "Revenue");

    setText("mix-vehicle", bestVehicle || "--");
    setText("mix-transmission", bestTransmission || "--");
    setText("mix-fuel", bestFuel || "--");
    setText("mix-strongest", strongestMix || "--");

    const vehicleTypes = [...new Set(data.map((item) => item.Vehicle_Type))].sort((a, b) => a.localeCompare(b));
    const fuelTypes = [...new Set(data.map((item) => item.Fuel_Type))].sort((a, b) => a.localeCompare(b));
    const zValues = vehicleTypes.map((vehicle) =>
        fuelTypes.map((fuel) =>
            sum(
                data
                    .filter((item) => item.Vehicle_Type === vehicle && item.Fuel_Type === fuel)
                    .map((item) => item.Sales_Volume)
            )
        )
    );

    Plotly.newPlot(
        "product-mix-chart",
        [
            {
                type: "heatmap",
                z: zValues,
                x: fuelTypes,
                y: vehicleTypes,
                colorscale: [
                    [0, "#08111b"],
                    [0.25, "#123763"],
                    [0.5, "#1d75d8"],
                    [0.75, "#4cc9f0"],
                    [1, "#ff4d57"],
                ],
                hovertemplate: "Vehicle Type: %{y}<br>Fuel Type: %{x}<br>Sales Volume: %{z:,.0f}<extra></extra>",
                colorbar: {
                    title: "Sales Volume",
                    tickfont: { color: "#dbe4ef" },
                    titlefont: { color: "#dbe4ef" },
                },
            },
        ],
        {
            margin: { l: 28, r: 18, t: 20, b: 20 },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            font: { color: "#dbe4ef", family: "Manrope" },
            xaxis: { side: "top" },
        },
        { displayModeBar: false, responsive: true }
    );
}

function summarizeModel(rows) {
    return {
        averagePrice: average(rows.map((item) => item.Price_USD)),
        totalSales: sum(rows.map((item) => item.Sales_Volume)),
        totalRevenue: sum(rows.map((item) => item.Revenue)),
        mileage: average(rows.map((item) => item.Claimed_Mileage)),
        engine: average(rows.map((item) => item.Engine_Size_L)),
        fuelType: mode(rows.map((item) => item.Fuel_Type)),
        transmission: mode(rows.map((item) => item.Transmission)),
        vehicleType: mode(rows.map((item) => item.Vehicle_Type)),
    };
}

function summarizeByKey(rows, key) {
    const grouped = groupBy(rows, key);
    return Object.fromEntries(
        Object.entries(grouped).map(([bucketKey, bucketRows]) => [bucketKey, summarizeModel(bucketRows)])
    );
}

function findTopKey(rows, key, metric) {
    const grouped = groupBy(rows, key);
    let bestKey = null;
    let bestValue = -Infinity;

    Object.entries(grouped).forEach(([bucketKey, bucketRows]) => {
        const total = sum(bucketRows.map((row) => row[metric]));
        if (total > bestValue) {
            bestValue = total;
            bestKey = bucketKey;
        }
    });

    return bestKey;
}

function findTopAverageKey(rows, key, metric) {
    const grouped = groupBy(rows, key);
    let bestKey = null;
    let bestValue = -Infinity;

    Object.entries(grouped).forEach(([bucketKey, bucketRows]) => {
        const avg = average(bucketRows.map((row) => row[metric]));
        if (avg > bestValue) {
            bestValue = avg;
            bestKey = bucketKey;
        }
    });

    return bestKey;
}

function findTopCombination(rows, keys, metric) {
    const grouped = {};
    rows.forEach((row) => {
        const bucketKey = keys.map((key) => row[key]).join(" | ");
        if (!grouped[bucketKey]) {
            grouped[bucketKey] = 0;
        }
        grouped[bucketKey] += row[metric];
    });

    return Object.entries(grouped).sort((a, b) => b[1] - a[1])[0]?.[0] ?? null;
}

function groupBy(rows, key) {
    return rows.reduce((accumulator, row) => {
        const bucket = row[key];
        if (!accumulator[bucket]) {
            accumulator[bucket] = [];
        }
        accumulator[bucket].push(row);
        return accumulator;
    }, {});
}

function groupByMany(rows, keys) {
    return rows.reduce((accumulator, row) => {
        const bucketKey = keys.map((key) => row[key]).join("::");
        if (!accumulator[bucketKey]) {
            accumulator[bucketKey] = [];
        }
        accumulator[bucketKey].push(row);
        return accumulator;
    }, {});
}

function bindPageButtons() {
    const buttons = document.querySelectorAll(".page-button");
    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            buttons.forEach((item) => item.classList.remove("active"));
            button.classList.add("active");

            appState.activePage = {
                label: button.dataset.pageLabel,
                id: button.dataset.pageId,
            };

            switchPowerBIPage(appState.activePage.id, appState.activePage.label);
        });
    });
}

function switchPowerBIPage(pageId, pageLabel) {
    const iframe = document.getElementById("powerbi-frame");
    const url = new URL(POWER_BI_BASE_URL);
    url.searchParams.set("navContentPaneEnabled", "false");
    url.searchParams.set("filterPaneEnabled", "false");
    url.searchParams.set("pageName", pageId);
    iframe.src = url.toString();

    setText("active-report-label", pageLabel);
    setFooterStatus(`Power BI page switched to ${pageLabel}.`);
}

function renderEmptyCharts() {
    const emptyLayout = {
        margin: { l: 20, r: 20, t: 30, b: 20 },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: "#a7b7ca", family: "Manrope" },
        xaxis: { visible: false },
        yaxis: { visible: false },
        annotations: [
            {
                text: "No matching data",
                x: 0.5,
                y: 0.5,
                xref: "paper",
                yref: "paper",
                showarrow: false,
                font: { size: 16, color: "#dbe4ef" },
            },
        ],
    };

    Plotly.newPlot("model-radar-chart", [], emptyLayout, { displayModeBar: false, responsive: true });
    Plotly.newPlot("regional-bubble-chart", [], emptyLayout, { displayModeBar: false, responsive: true });
    Plotly.newPlot("product-mix-chart", [], emptyLayout, { displayModeBar: false, responsive: true });
}

function revealSections() {
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");
                }
            });
        },
        { threshold: 0.14 }
    );

    document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));
}

function sum(values) {
    return values.reduce((total, value) => total + Number(value || 0), 0);
}

function average(values) {
    if (!values.length) {
        return 0;
    }
    return sum(values) / values.length;
}

function mode(values) {
    const counts = values.reduce((accumulator, value) => {
        const key = value || "Unknown";
        accumulator[key] = (accumulator[key] || 0) + 1;
        return accumulator;
    }, {});

    return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "Unknown";
}

function normalizeAgainst(value, maxValue) {
    if (!maxValue) {
        return 0;
    }
    return Number(((value / maxValue) * 100).toFixed(1));
}

function scaleBubble(value) {
    return Math.max(16, Math.min(58, Math.sqrt(value) / 180));
}

function formatCurrency(value) {
    const absolute = Math.abs(value);
    if (absolute >= 1_000_000_000_000) return `$${(value / 1_000_000_000_000).toFixed(2)}T`;
    if (absolute >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}B`;
    if (absolute >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
    if (absolute >= 1_000) return `$${(value / 1_000).toFixed(2)}K`;
    return `$${value.toFixed(0)}`;
}

function formatCompact(value) {
    const absolute = Math.abs(value);
    if (absolute >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B`;
    if (absolute >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`;
    if (absolute >= 1_000) return `${(value / 1_000).toFixed(2)}K`;
    return `${Math.round(value)}`;
}

function setText(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

function setFooterStatus(text) {
    setText("footer-status", text);
}

function escapeHtml(value) {
    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
