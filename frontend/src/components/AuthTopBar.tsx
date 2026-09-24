import LanguageSwitcher from "./LanguageSwitcher";
import { TopBarMenuProvider } from "../context/TopBarMenuContext";

// The pre-header floating language switcher, kept for the auth pages
// (login/register), which intentionally don't show the app header.
export default function AuthTopBar() {
  return (
    <div className="auth-top-bar">
      <TopBarMenuProvider>
        <LanguageSwitcher />
      </TopBarMenuProvider>
    </div>
  );
}
