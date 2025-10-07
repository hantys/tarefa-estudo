"use client"

import "../../styles/globals.css"
import Link from "next/link";

import { useSession, signIn, signOut } from "next-auth/react";

export default function Header() {

  const { data: session, status } = useSession();

  return (
    <>
      <header className="header">
        <section className="content">
          <nav className="nav">
            <Link href="/">
              <h1 className="logo">
                Tarefas<span>+</span>
              </h1>
            </Link>
            {session ? (
              <Link href="/dashboard">
                <button className="link">
                  Meu Painel
                </button>
              </Link>
            ) : <></>}
          </nav>

          {status === 'loading' ? (
            <span>Carregando...</span>
          ) : session ? (
            <button className="loginButton" onClick={() => signOut()}>
              Olá {session.user?.name}
            </button>
          ) : (
            <button className="loginButton" onClick={() => signIn('google')}>
              Acessar
            </button>
          )}
        </section>
      </header>
    </>
  );
}