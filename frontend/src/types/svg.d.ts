declare module "*.svg" {
  const content: string;
  export default content;
}

declare module "*.svg?url" {
  const content: string;
  export default content;
}

declare module "*.svg?component" {
  import React from "react";
  const SVGComponent: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  export default SVGComponent;
} 