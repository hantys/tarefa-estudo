import "../styles/globals.css";
import Header from "../components/header";
import SessionProviderWrapper from "../components/SessionProviderWrapper"
interface IProps{
  children: React.ReactNode
}

export default function RootLayout({
  children,
}: IProps) {
  return (
    <html lang="pt-BR">
      <body>
        <SessionProviderWrapper>
          <Header />
          <div className="container">
            {children}
          </div>
        </SessionProviderWrapper>
      </body>
    </html>
  );
}
