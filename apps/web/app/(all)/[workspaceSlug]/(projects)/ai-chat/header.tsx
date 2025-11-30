"use client";

import { observer } from "mobx-react";
// plane imports
import { useTranslation } from "@plane/i18n";
import { AiIcon } from "@plane/propel/icons";
import { Breadcrumbs, Header } from "@plane/ui";
// components
import { BreadcrumbLink } from "@/components/common/breadcrumb-link";

export const AIChatHeader = observer(() => {
  // plane hooks
  const { t } = useTranslation();

  return (
    <Header>
      <Header.LeftItem>
        <div className="flex items-center gap-2">
          <Breadcrumbs>
            <Breadcrumbs.Item
              component={
                <BreadcrumbLink
                  label="AI"
                  icon={<AiIcon className="h-4 w-4 text-custom-text-300" />}
                />
              }
            />
          </Breadcrumbs>
        </div>
      </Header.LeftItem>
      <Header.RightItem>
        {/* Right side actions can be added here */}
      </Header.RightItem>
    </Header>
  );
});

