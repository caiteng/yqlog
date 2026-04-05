(() => {
  const detectAnomalyIndexes = (values) => {
    if (!Array.isArray(values) || values.length < 5) return [];

    const avg = values.reduce((sum, value) => sum + value, 0) / values.length;
    const variance = values.reduce((sum, value) => sum + ((value - avg) ** 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);

    return values
      .map((value, index) => {
        const prev = index > 0 ? values[index - 1] : value;
        const dropRate = prev > 0 ? (prev - value) / prev : 0;
        const score = stdDev > 0 ? Math.abs(value - avg) / stdDev : 0;
        const isAnomaly = score >= 1.25 || dropRate >= 0.32;
        return isAnomaly ? index : -1;
      })
      .filter((index) => index >= 0);
  };

  const formatDateLabel = (dateStr) => {
    if (!dateStr) return '';
    const [year, month, day] = dateStr.split('-');
    if (!year || !month || !day) return dateStr;
    return `${month}/${day}`;
  };

  window.YQLogCharts = {
    detectAnomalyIndexes,
    formatDateLabel,
  };
})();
