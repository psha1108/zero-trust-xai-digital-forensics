export const formatDateIST = (dateString) => {
  if (!dateString) return "Not available";
  
  let isoString = dateString;
  if (typeof isoString === 'string' && isoString.includes('T') && !isoString.endsWith('Z') && !isoString.includes('+') && !isoString.substring(isoString.indexOf('T')).includes('-')) {
    isoString += 'Z';
  }
  
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return "Not available";
  
  const options = {
    timeZone: 'Asia/Kolkata',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
    timeZoneName: 'short'
  };
  
  return new Intl.DateTimeFormat('en-GB', options).format(date);
};
