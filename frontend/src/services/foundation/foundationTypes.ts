/* src/services/foundation/foundationTypes.ts */

export interface FoundationEnum {
  key: string;
  label: string;
  description?: string;
}

export interface FoundationMetadata {
  roles: FoundationEnum[];
  permissions: FoundationEnum[];
  statuses: FoundationEnum[];
}
