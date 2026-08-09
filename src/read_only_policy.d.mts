export function readOnlyRejection(action: string): {
  readonly error: string;
  readonly code: "READ_ONLY_PRODUCT";
};
