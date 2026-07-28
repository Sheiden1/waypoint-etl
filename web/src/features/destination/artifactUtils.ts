export function artifactExpirationLabel(seconds?: number): string {
  if (seconds === undefined || seconds <= 0) {
    return "A disponibilidade dos downloads não foi informada pela API.";
  }
  if (seconds < 60) {
    return "Os downloads ficam disponíveis por menos de 1 minuto após a execução.";
  }

  const minutes = Math.ceil(seconds / 60);
  if (minutes < 60) {
    return `Os downloads ficam disponíveis por ${minutes} minuto${
      minutes === 1 ? "" : "s"
    } após a execução.`;
  }

  const hours = Math.ceil(minutes / 60);
  return `Os downloads ficam disponíveis por ${hours} hora${
    hours === 1 ? "" : "s"
  } após a execução.`;
}
