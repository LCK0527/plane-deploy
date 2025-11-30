"use client";

import { observer } from "mobx-react";
// plane imports
import { useTranslation } from "@plane/i18n";
import { AppHeader } from "@/components/core/app-header";
import { ContentWrapper } from "@/components/core/content-wrapper";
import { PageHead } from "@/components/core/page-title";
import { Breadcrumbs, Header } from "@plane/ui";
// components
import { AIChatView } from "@/components/ai-chat/root";
// hooks
import { useWorkspace } from "@/hooks/store/use-workspace";
// local components
import { AIChatHeader } from "./header";

const AIChatPage = observer(() => {
  const { currentWorkspace } = useWorkspace();
  const { t } = useTranslation();
  // derived values
  const pageTitle = currentWorkspace?.name ? `${currentWorkspace?.name} - AI Chat` : undefined;

  return (
    <>
      <AppHeader header={<AIChatHeader />} />
      <ContentWrapper>
        <PageHead title={pageTitle} />
        <AIChatView />
      </ContentWrapper>
    </>
  );
});

export default AIChatPage;

