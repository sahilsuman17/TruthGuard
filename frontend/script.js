const analyzeBtn =
    document.getElementById("analyzeBtn");

const newsText =
    document.getElementById("newsText");

const loading =
    document.getElementById("loading");

const result =
    document.getElementById("result");

const resultStatus =
    document.getElementById("resultStatus");

const confidence =
    document.getElementById("confidence");

const fakeProbability =
    document.getElementById("fakeProbability");

const realProbability =
    document.getElementById("realProbability");

const fakeBar =
    document.getElementById("fakeBar");

const realBar =
    document.getElementById("realBar");

const charCount =
    document.getElementById("charCount");

const historyList =
    document.getElementById("historyList");

const clearHistory =
    document.getElementById("clearHistory");



/* =====================================================
   CHARACTER COUNTER
===================================================== */

newsText.addEventListener(
    "input",
    () => {

        const length =
            newsText.value.length;

        charCount.textContent =
            `${length.toLocaleString()} characters`;

    }
);



/* =====================================================
   ANALYZE NEWS
===================================================== */

analyzeBtn.addEventListener(
    "click",
    async () => {

        const text =
            newsText.value.trim();


        if (!text) {

            alert(
                "Please enter a news article or headline."
            );

            newsText.focus();

            return;
        }


        analyzeBtn.disabled = true;

        analyzeBtn.innerHTML =
            "⏳ Analyzing...";

        loading.classList.remove(
            "hidden"
        );

        result.classList.add(
            "hidden"
        );


        try {

            const response =
                await fetch(
                    "http://127.0.0.1:8000/predict",
                    {

                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            text: text
                        })

                    }
                );


            if (!response.ok) {

                throw new Error(
                    `Server returned ${response.status}`
                );

            }


            const data =
                await response.json();


            console.log(
                "TruthGuard API Response:",
                data
            );


            const fake =
                Number(
                    data.fake_probability
                );

            const real =
                Number(
                    data.real_probability
                );

            const score =
                Number(
                    data.confidence
                );


            resultStatus.textContent =
                data.prediction;


            confidence.textContent =
                `${score.toFixed(2)}%`;


            fakeProbability.textContent =
                `${fake.toFixed(2)}%`;


            realProbability.textContent =
                `${real.toFixed(2)}%`;


            fakeBar.style.width =
                "0%";

            realBar.style.width =
                "0%";


            requestAnimationFrame(
                () => {

                    requestAnimationFrame(
                        () => {

                            fakeBar.style.width =
                                `${fake}%`;

                            realBar.style.width =
                                `${real}%`;

                        }
                    );

                }
            );


            if (
                data.prediction ===
                "Potentially Misleading"
            ) {

                resultStatus.style.color =
                    "#ef4444";

                confidence.style.borderColor =
                    "#ef4444";

            }

            else {

                resultStatus.style.color =
                    "#22c55e";

                confidence.style.borderColor =
                    "#22c55e";

            }


            result.classList.remove(
                "hidden"
            );


            /* SAVE HISTORY */

            saveAnalysisHistory(
                text,
                data.prediction,
                score
            );


            /* UPDATE DASHBOARD */

            updateDashboard();


        }


        catch (error) {

            console.error(
                "TruthGuard Error:",
                error
            );


            alert(
                "Unable to connect to TruthGuard server.\n\n" +
                "Make sure FastAPI is running on port 8000."
            );

        }


        finally {

            loading.classList.add(
                "hidden"
            );

            analyzeBtn.disabled =
                false;

            analyzeBtn.innerHTML =
                "🔍 Analyze News";

        }

    }
);



/* =====================================================
   SAVE HISTORY
===================================================== */

function saveAnalysisHistory(
    text,
    prediction,
    confidenceValue
) {

    const history =
        JSON.parse(
            localStorage.getItem(
                "truthguardHistory"
            ) || "[]"
        );


    const item = {

        text: text,

        prediction: prediction,

        confidence: confidenceValue,

        time:
            new Date().toLocaleString()

    };


    history.unshift(item);


    const limitedHistory =
        history.slice(0, 10);


    localStorage.setItem(
        "truthguardHistory",
        JSON.stringify(
            limitedHistory
        )
    );


    displayHistory();

}



/* =====================================================
   DISPLAY HISTORY
===================================================== */

function displayHistory() {

    if (!historyList) {
        return;
    }


    const history =
        JSON.parse(
            localStorage.getItem(
                "truthguardHistory"
            ) || "[]"
        );


    if (history.length === 0) {

        historyList.innerHTML = `

            <div class="history-empty">

                <span>📰</span>

                <p>
                    No analyses yet.
                </p>

                <small>
                    Analyze a news article to see it here.
                </small>

            </div>

        `;

        return;
    }


    historyList.innerHTML =
        history.map(
            (item) => {

                const isFake =
                    item.prediction ===
                    "Potentially Misleading";


                return `

                    <div class="history-item">

                        <div class="history-item-top">

                            <span
                                class="history-prediction ${
                                    isFake
                                        ? "fake"
                                        : "real"
                                }"
                            >

                                ${
                                    isFake
                                        ? "⚠️ Potentially Misleading"
                                        : "✅ Likely Reliable"
                                }

                            </span>


                            <span class="history-confidence">

                                ${Number(
                                    item.confidence
                                ).toFixed(2)}%

                            </span>

                        </div>


                        <p class="history-text">

                            ${escapeHTML(
                                item.text
                            )}

                        </p>


                        <div class="history-time">

                            🕒 ${escapeHTML(
                                item.time
                            )}

                        </div>

                    </div>

                `;

            }
        ).join("");

}



/* =====================================================
   SAFE HTML
===================================================== */

function escapeHTML(text) {

    const div =
        document.createElement(
            "div"
        );

    div.textContent =
        String(text);

    return div.innerHTML;

}



/* =====================================================
   CLEAR HISTORY
===================================================== */

if (clearHistory) {

    clearHistory.addEventListener(
        "click",
        () => {

            const confirmClear =
                confirm(
                    "Clear all TruthGuard analysis history?"
                );


            if (!confirmClear) {
                return;
            }


            localStorage.removeItem(
                "truthguardHistory"
            );


            displayHistory();


            updateDashboard();

        }
    );

}



/* =====================================================
   DASHBOARD
===================================================== */

function updateDashboard() {

    const history =
        JSON.parse(
            localStorage.getItem(
                "truthguardHistory"
            ) || "[]"
        );


    const total =
        history.length;


    let reliable = 0;

    let misleading = 0;

    let confidenceTotal = 0;


    history.forEach(
        (item) => {

            if (
                item.prediction ===
                "Potentially Misleading"
            ) {

                misleading++;

            }

            else {

                reliable++;

            }


            confidenceTotal +=
                Number(
                    item.confidence
                ) || 0;

        }
    );


    const averageConfidence =
        total > 0
            ? confidenceTotal / total
            : 0;


    const reliablePercentage =
        total > 0
            ? (reliable / total) * 100
            : 0;


    const misleadingPercentage =
        total > 0
            ? (misleading / total) * 100
            : 0;



    /* ================= COUNTERS ================= */

    const totalElement =
        document.getElementById(
            "totalAnalyses"
        );

    const reliableElement =
        document.getElementById(
            "reliableAnalyses"
        );

    const misleadingElement =
        document.getElementById(
            "misleadingAnalyses"
        );

    const averageElement =
        document.getElementById(
            "averageConfidence"
        );


    if (totalElement) {

        totalElement.textContent =
            total;

    }


    if (reliableElement) {

        reliableElement.textContent =
            reliable;

    }


    if (misleadingElement) {

        misleadingElement.textContent =
            misleading;

    }


    if (averageElement) {

        averageElement.textContent =
            `${averageConfidence.toFixed(2)}%`;

    }



    /* ================= PERCENTAGES ================= */

    const reliablePercentageElement =
        document.getElementById(
            "reliablePercentage"
        );

    const misleadingPercentageElement =
        document.getElementById(
            "misleadingPercentage"
        );


    if (reliablePercentageElement) {

        reliablePercentageElement.textContent =
            `${reliablePercentage.toFixed(2)}%`;

    }


    if (misleadingPercentageElement) {

        misleadingPercentageElement.textContent =
            `${misleadingPercentage.toFixed(2)}%`;

    }



    /* ================= BARS ================= */

    const reliableBar =
        document.getElementById(
            "reliableDistributionBar"
        );

    const misleadingBar =
        document.getElementById(
            "misleadingDistributionBar"
        );


    if (reliableBar) {

        reliableBar.style.width =
            `${reliablePercentage}%`;

    }


    if (misleadingBar) {

        misleadingBar.style.width =
            `${misleadingPercentage}%`;

    }



    /* ================= EMPTY STATE ================= */

    const dashboardEmpty =
        document.getElementById(
            "dashboardEmpty"
        );


    if (dashboardEmpty) {

        if (total === 0) {

            dashboardEmpty.classList.remove(
                "hidden"
            );

        }

        else {

            dashboardEmpty.classList.add(
                "hidden"
            );

        }

    }

}



/* =====================================================
   INITIAL LOAD
===================================================== */

displayHistory();

updateDashboard();