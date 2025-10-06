
import Image from "next/image";

export default function Home() {
  return (
    <>
      <main className="main">
        <div className="logoContent">
          <Image
            className="hero"
            src="/assets/hero.png"
            alt="Hero Image"
            priority
            width={100}
            height={100}
          />
        </div>
      </main>
      <h1 className="title">Sistema feito para você organizar
        <br /> seus estudos e tarefas
      </h1>

      <div>
        +12 posts
      </div>

      <div>
        +90 comentarios
      </div>
    </>
  );
}