export function readOnlyRejection(action) {
  return {
    error: `${action} is unavailable: AIR ArdhaMind is read only.`,
    code: "READ_ONLY_PRODUCT",
  };
}
